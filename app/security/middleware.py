# security/middleware.py
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from datetime import datetime
import logging
import json
import random
from django.utils import timezone
from django.conf import settings
import os
import re
from urllib.parse import urlparse

logger = logging.getLogger('security')

class SecurityLogFormatter:
    @staticmethod
    def format_log_message(ip, request, attack_type, attempt_count):
        return {
            '🚨 Alert': 'ALERTE SÉCURITÉ',
            '🎯 Type': f"Tentative de {attack_type}",
            '🌐 IP': ip,
            '🔍 Path': request.path,
            '📝 Method': request.method,
            '🌍 User-Agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            '📊 Tentative': f"#{attempt_count}",
            '⏰ Timestamp': timezone.now().isoformat(),
            '📍 Referer': request.META.get('HTTP_REFERER', 'Direct'),
            '🔑 Headers': dict(request.headers),
        }

class TrollingSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs de troll
        self.troll_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll Classic
            "https://www.youtube.com/watch?v=L_jWHffIx5E",  # All Star - Smash Mouth
            "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
            "https://www.youtube.com/watch?v=y6120QOlsfU",  # Sandstorm
            "https://www.youtube.com/watch?v=ZZ5LpwO-An4",  # HEYYEYAAEYAAAEYAEYAA
            "https://www.youtube.com/watch?v=G1IbRujko-A",  # Nyan Cat
        ]

        # Messages humoristiques
        self.funny_messages = [
            "Bien essayé, mais notre sécurité est plus têtue qu'un bug en production 😎",
            "404 - Hackers qualifiés non trouvés 🤷‍♂️",
            "Oups ! Vous venez de gagner un ticket gratuit pour le Rick Roll Express 🎵",
            "Loading hacking_prevention.exe... SUCCÈS ! 🚫",
            "Error 418: I'm a teapot (et je ne compile pas de code malveillant) ☕",
            "Hack.exe a cessé de fonctionner. Windows recherche une solution... 🪟",
            "sudo apt-get install better-hacking-skills 📚",
            "pip install try-harder 😉",
            "npm install --save hack-prevention (100% de dépendances sécurisées) 🛡️",
            "git commit -m 'Nice try, better luck next time' 🎮",
            "Error 500: Server too busy playing Minecraft 🎲",
            "Firewall.exe has stopped working... JK, got you! 🎯",
            "Loading counter_hack.dll... Hacker neutralized! 🎳",
            "Sorry, our server is too busy watching cat videos 🐱",
            "Task failed successfully! Try again never 🎪",
        ]

        # 1. Patterns WordPress et CMS
        self.wordpress_patterns = [
            'wp-admin', 'wp-content', 'wp-includes',
            'xmlrpc.php', 'wp-login', 'wp-config',
            'wlwmanifest', 'wp-json', 'wp-cron',
            'wp-mail', 'wp-links', 'wp-load',
            'joomla', 'drupal', 'magento',
            'wordpress', 'wp-plugins', 'wp-themes',
        ]
        
        # 2. Fichiers de Configuration Sensibles
        self.config_patterns = [
            'config.php', 'configuration.php', 'settings.php',
            'setup.php', 'install.php', 'admin.php',
            'administrator', 'admincp', 'cpanel',
            'phpmyadmin', 'myadmin', 'mysql',
            'database.php', 'db.php', 'sql.php',
            '.env', '.git', '.htaccess', '.ssh',
            'config.js', 'settings.js', 'web.config',
            'credentials', 'secret', 'password',
            'deploy', 'backup', '.svn', '.hg',
        ]
        
        # 3. Extensions Sensibles
        self.extension_patterns = [
            '.php', '.asp', '.aspx', '.jsp', '.jspx',
            '.swp', '.swf', '.git', '.svn', '.hg',
            '.env', '.htaccess', '.htpasswd', '.user.ini',
            '.sql', '.bak', '.backup', '.old', '.temp',
            '.txt', '.log', '.conf', '.config', '.ini',
            '.dll', '.exe', '.sh', '.bash', '.py',
            '.pl', '.cgi', '.cfm', '.log', '.bak',
        ]
        
        # 4. Chemins Administratifs
        self.admin_patterns = [
            'admin', 'administrator', 'admincp', 'adminer',
            'moderator', 'webadmin', 'backoffice', 'manager',
            'phpinfo', 'dashboard', 'cms', 'control',
            'panel', 'console', 'sysadmin', 'root',
            'supervisor', 'manager', 'manage', 'administration',
            'backend', 'private', 'secret', 'restricted',
            'signin', 'setup', 'install',
        ]
        
        # 5. Patterns d'Attaque Standards
        self.attack_patterns = [
            'shell', 'backdoor', 'malware', 'exploit',
            'hack', 'passwd', 'password', 'admin',
            'setup', 'webhook', 'backup', 'install',
            'upgrade', 'update', 'debug', 'trace',
            'eval', 'exec', 'system', 'cmd',
            'command', 'execute', 'ping', 'nmap',
        ]

        # 6. Patterns SQL Injection
        self.sql_injection_patterns = [
            'union select', 'information_schema', 
            'sysdatabases', 'sysusers', 'sys.users',
            'concat(', 'group_concat', 'load_file',
            'benchmark(', 'sleep(', 'delay',
            'order by', 'group by', 'having',
            'waitfor delay', 'varchar(', 'cast(',
            'declare', 'drop table', 'truncate',
            'delete from', 'insert into', 'select from',
        ]

        # 7. Patterns XSS
        self.xss_patterns = [
            '<script', 'javascript:', 'vbscript:',
            'onload=', 'onerror=', 'onclick=',
            'onmouseover=', 'onfocus=', 'onblur=',
            'alert(', 'console.log(', 'eval(',
            'document.cookie', 'document.write',
            'innerHTML', 'outerHTML', 'href=javascript',
        ]

        # 8. Patterns Shell et Command Injection
        self.shell_patterns = [
            ';', '&&', '||', '|', '`',
            '$(',  '${', 'sudo', 'chmod',
            'chown', 'rm -rf', 'mv', 'cp',
            'cat', 'echo', 'wget', 'curl',
            'bash', 'sh', 'python', 'perl',
        ]

        # 9. File Inclusion Patterns
        self.file_inclusion_patterns = [
            '../', '..%2f', '%2e%2e%2f',
            'file://', 'input://', 'data://',
            'php://', 'zip://', 'phar://',
            'expect://', 'glob://', 'compress.zlib://',
        ]

        # 10. Scan et Enumeration Patterns
        self.scan_patterns = [
            'scanner', 'nikto', 'nmap',
            'wpscan', 'sqlmap', 'dirbuster',
            'gobuster', 'burp', 'acunetix',
            'nessus', 'whatweb', 'reconnaissance',
            'enum', 'hydra', 'brutus',
        ]

        # Combiner tous les patterns
        self.all_patterns = (
            self.wordpress_patterns +
            self.config_patterns +
            self.extension_patterns +
            self.admin_patterns +
            self.attack_patterns +
            self.sql_injection_patterns +
            self.xss_patterns +
            self.shell_patterns +
            self.file_inclusion_patterns +
            self.scan_patterns
        )

        # Configuration du tracking
        self.attempt_tracker = {}
        self.max_attempts = 5
        self.block_duration = 3600  # 1 heure
        self.blocked_ips = {}
        self.suspicious_ips = {}
        self.last_cleanup = datetime.now().timestamp()
        
    def get_client_ip(self, request):
        """Obtient l'IP réelle du client en tenant compte des proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def clean_old_records(self):
        """Nettoie périodiquement les enregistrements"""
        current_time = datetime.now().timestamp()
        
        # Nettoyage toutes les 6 heures
        if current_time - self.last_cleanup > 21600:
            expired_ips = [
                ip for ip, block_time in self.blocked_ips.items() 
                if current_time > block_time
            ]
            for ip in expired_ips:
                del self.blocked_ips[ip]
                logger.info(f"🧹 Déblocage automatique de l'IP: {ip}")

            self.attempt_tracker = {
                ip: count for ip, count in self.attempt_tracker.items()
                if ip not in expired_ips
            }
            
            self.suspicious_ips = {
                ip: data for ip, data in self.suspicious_ips.items()
                if current_time - data['last_seen'] < 86400  # 24 heures
            }
            
            self.last_cleanup = current_time

    def is_path_suspicious(self, path):
        """Vérifie si le chemin contient des patterns suspects"""
        path_lower = path.lower()
        
        # Vérification basique des patterns
        if any(pattern in path_lower for pattern in self.all_patterns):
            return True
            
        # Vérification des caractères suspects
        suspicious_chars = re.compile(r'[<>\'"]|\.\.|%00|\\x|\\u')
        if suspicious_chars.search(path):
            return True
            
        # Vérification de la longueur excessive
        if len(path) > 255:
            return True
            
        return False

    def get_funny_response(self, attack_type):
        """Génère une réponse humoristique basée sur le type d'attaque"""
        attack_responses = {
            "WordPress Scan": "WordPress ? Désolé, on utilise Django. Essayez pip install better-scanning 😉",
            "Configuration Access": "Configurer quoi ? Notre sens de l'humour ? 🤔",
            "Admin Access": "sudo permission-denied && echo 'Bien essayé!' 🎯",
            "Direct Attack": "chmod 000 piratage.txt # Accès refusé avec style 😎",
            "Upload Access": "virus.exe was not uploaded successfully 🦠",
            "SQL Injection": "DROP TABLE hacker; -- Tentative supprimée 😎",
            "XSS Attack": "<script>alert('Nice Try!')</script> est bloqué ici 🛡️",
            "Shell Injection": "rm -rf /hackers_attempt/* 🗑️",
            "File Inclusion": "Error 404: Inclusion not found 📁",
            "Scanner Detection": "Nmap ? Plus comme Nope ! 🚫",
        }
        return attack_responses.get(attack_type, random.choice(self.funny_messages))

    def detect_attack_type(self, path, request_data=None):
        """Détection améliorée du type d'attaque"""
        path_lower = path.lower()
        
        # Vérification des différents types d'attaques
        if any(p in path_lower for p in self.wordpress_patterns):
            return "WordPress Scan"
        elif any(p in path_lower for p in self.sql_injection_patterns):
            return "SQL Injection"
        elif any(p in path_lower for p in self.xss_patterns):
            return "XSS Attack"
        elif any(p in path_lower for p in self.shell_patterns):
            return "Shell Injection"
        elif any(p in path_lower for p in self.file_inclusion_patterns):
            return "File Inclusion"
        elif any(p in path_lower for p in self.scan_patterns):
            return "Scanner Detection"
        elif any(p in path_lower for p in self.config_patterns):
            return "Configuration Access"
        elif any(p in path_lower for p in self.admin_patterns):
            return "Admin Access"
        return "Unknown Attack Pattern"

    def analyze_request(self, request):
        """Analyse approfondie de la requête"""
        suspicious_score = 0
        reasons = []

        # Vérifier le User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) < 10:
            suspicious_score += 2
            reasons.append("User-Agent suspect")

        # Vérifier le Referer pour les requêtes non-GET
        if request.method != 'GET':
            referer = request.META.get('HTTP_REFERER', '')
            if referer:
                parsed_referer = urlparse(referer)
                if parsed_referer.netloc not in [request.get_host()]:
                    suspicious_score += 1
                    reasons.append("Referer suspect")

        # Vérifier les en-têtes courants
        common_headers = ['Accept', 'Accept-Language', 'Accept-Encoding']
        missing_headers = sum(1 for header in common_headers if header not in request.META)
        if missing_headers > 1:
            suspicious_score += missing_headers
            reasons.append(f"En-têtes manquants: {missing_headers}")

        # Vérifier les paramètres de requête suspects
        if request.GET:
            if any(pattern in str(request.GET).lower() for pattern in self.all_patterns):
                suspicious_score += 2
                reasons.append("Paramètres GET suspects")

        if request.POST:
            if any(pattern in str(request.POST).lower() for pattern in self.all_patterns):
                suspicious_score += 3
                reasons.append("Paramètres POST suspects")

        return suspicious_score, reasons

    def log_attempt(self, request, ip, attack_type):
        """Log amélioré avec formatage et emojis"""
        log_data = SecurityLogFormatter.format_log_message(
            ip=ip,
            request=request,
            attack_type=attack_type,
            attempt_count=self.attempt_tracker.get(ip, 1)
        )
        
        # Ajout de l'analyse de la requête
        suspicious_score, reasons = self.analyze_request(request)
        log_data['🔍 Analyse'] = {
            'score': suspicious_score,
            'raisons': reasons
        }
        
        # Log au format WARNING avec indentation JSON
        logger.warning(json.dumps(log_data, indent=2, ensure_ascii=False))
        
        # Log supplémentaire pour les tentatives multiples
        if self.attempt_tracker.get(ip, 1) > 3:
            logger.error(
                f"🚨 ALERTE MULTIPLE: {ip} a fait {self.attempt_tracker[ip]} tentatives! "
                f"Score de suspicion: {suspicious_score}"
            )

    def __call__(self, request):
        # Nettoyage périodique
        self.clean_old_records()
        
        ip = self.get_client_ip(request)
        path = request.path.lstrip('/').lower()

        # Vérification du blocage
        if ip in self.blocked_ips:
            if datetime.now().timestamp() < self.blocked_ips[ip]:
                logger.warning(f"🚫 Tentative d'accès bloquée pour l'IP: {ip}")
                return HttpResponseForbidden(
                    "🎵 You've been blocked! Time to listen to some music... 🎵"
                )
            else:
                del self.blocked_ips[ip]

        # Analyse de la requête
        suspicious_score, reasons = self.analyze_request(request)
        
        # Vérification du chemin suspect
        is_suspicious = self.is_path_suspicious(path)
        
        if is_suspicious or suspicious_score > 3:
            attack_type = self.detect_attack_type(path, request.POST or request.GET)
            self.attempt_tracker[ip] = self.attempt_tracker.get(ip, 0) + 1
            
            # Mise à jour des données de surveillance
            self.suspicious_ips[ip] = {
                'last_seen': datetime.now().timestamp(),
                'score': suspicious_score,
                'reasons': reasons
            }
            
            self.log_attempt(request, ip, attack_type)

            if self.attempt_tracker[ip] >= self.max_attempts:
                self.blocked_ips[ip] = datetime.now().timestamp() + self.block_duration
                return HttpResponseForbidden(
                    "🎮 Game Over! Trop de tentatives. Revenez plus tard avec de meilleures compétences! 🎮"
                )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'message': self.get_funny_response(attack_type),
                    'redirect': random.choice(self.troll_urls)
                })

            return redirect(random.choice(self.troll_urls))

        return self.get_response(request)