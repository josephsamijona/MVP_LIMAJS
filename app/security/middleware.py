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
        
        # Liste des chemins sûrs
        self.safe_paths = [
            # Django Admin
            '/admin/',
            '/admin/login/',
            '/admin/logout/',
            '/admin/password_change/',
            '/admin/jsi18n/',
            '/admin/auth/',
            '/admin/auth/user/',
            '/admin/auth/group/',
            
            # Static et Media
            '/static/',
            '/static/admin/',
            '/static/rest_framework/',
            '/media/',
            
            # API paths - Driver
            '/api/',
            '/api/driver/',
            '/api/driver/login/',
            '/api/driver/logout/',
            '/api/driver/profile/',
            '/api/driver/refresh/',
            '/api/drivera/login/',
            '/api/drivera/logout/',
            '/api/drivera/profile/',
            '/api/drivera/refresh/',

            # API Authentication
            '/api/token/',
            '/api/token/refresh/',
            '/api/auth/',
            '/api/auth/login/',
            '/api/auth/logout/',
            '/api/auth/password/reset/',
            '/api/auth/password/reset/confirm/',

            # API Documentation
            '/api/schema/',
            '/api/docs/',
            '/api/swagger/',
            '/api/swagger.json',
            '/api/swagger.yaml',
            '/api/redoc/',

            # Common Files
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml',
            '/manifest.json',
            '/.well-known/',

            # Debug Toolbar (en développement)
            '/__debug__/',
            
            # Health Checks
            '/health/',
            '/health/check/',
            '/ping/',

            # Common Static Paths
            '/static/css/',
            '/static/js/',
            '/static/img/',
            '/static/fonts/',
            '/static/icons/',
            '/media/uploads/',

            # Django Default Auth
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/profile/',
            '/accounts/password_reset/',

            # API Versioning
            '/api/v1/',
            '/api/v2/',
            '/api/latest/',
        ]
        
        # URLs de troll
        self.troll_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll Classic
            "https://www.youtube.com/watch?v=L_jWHffIx5E",  # All Star
            "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
            "https://www.youtube.com/watch?v=y6120QOlsfU",  # Sandstorm
            "https://www.youtube.com/watch?v=ZZ5LpwO-An4",  # HEYYEYAA
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
        ]

        # Patterns malveillants
        self.malicious_patterns = {
            # Remote File Inclusion et LFI
            'file_inclusion': [
                '../', '..%2f', '..\%u2216', '..\\', '..//',
                'file://', 'http://', 'ftp://', 'php://',
                '/etc/passwd', '/etc/shadow', '/etc/hosts',
                'C:\\Windows\\', 'C:\\Program Files\\',
                '/proc/self/', '/proc/version', '/proc/cpuinfo',
                '.htaccess', '.htpasswd', 'web.config',
                'wp-config.php', 'config.inc.php',
            ],

            # Injections SQL avancées
            'sql_injection': [
                'union select', 'information_schema', 
                'sysdatabases', 'sysusers', 'sys.users',
                'version()', 'database()', 'schema()',
                'user()', 'system_user()', 'session_user()',
                'SELECT @@', 'SHOW DATABASES', 'SHOW TABLES',
                'INTO OUTFILE', 'INTO DUMPFILE',
                'UNION ALL SELECT', 'UNION SELECT',
                'HAVING 1=1', 'HAVING 1=0',
                'CASE WHEN', 'IF(1=1', 'SLEEP(',
                'WAITFOR DELAY', 'BENCHMARK(',
                'concat(', 'group_concat', 'load_file',
                'benchmark(', 'sleep(', 'delay',
                'order by', 'group by', 'having',
                'waitfor delay', 'varchar(', 'cast(',
                'declare', 'drop table', 'truncate',
                'delete from', 'insert into', 'select from',
            ],

            # XSS Patterns
            'xss': [
                '<script', 'javascript:', 'vbscript:',
                'onload=', 'onerror=', 'onclick=',
                'onmouseover=', 'onfocus=', 'onblur=',
                'alert(', 'console.log(', 'eval(',
                'document.cookie', 'document.write',
                'innerHTML', 'outerHTML', 'href=javascript',
            ],

            # Webshells
            'webshell': [
                'c99.php', 'r57.php', 'cmd.php', 'shell.php',
                'b374k', 'weevely', 'chinese.php', 'phpspy',
                'wso.php', 'dq.php', 'az.php', 'bash.php',
                'system.php', 'cmd.asp', 'cmd.jsp',
                'syscmd.php', 'b374k.php', 'alfa.php',
            ],

            # Shell et Command Injection
            'shell': [
                ';', '&&', '||', '|', '`',
                '$(',  '${', 'sudo', 'chmod',
                'chown', 'rm -rf', 'mv', 'cp',
                'cat', 'echo', 'wget', 'curl',
                'bash', 'sh', 'python', 'perl',
            ],

            # Tentatives de Contournement
            'bypass_attempts': [
                '%00', '%0d%0a', '%0a', '%0d',
                '%252f', '%25252f', '%2e%2e%2f',
                'data:text/html', 'data:application/x-httpd',
                'base64,', 'php://input', 'zip://', 'phar://',
                'expect://', 'php://filter',
                'convert.base64-encode',
            ],

            # Fichiers Sensibles
            'sensitive_files': [
                'composer.json', 'package.json', 'yarn.lock',
                'Gemfile', 'requirements.txt', 'Pipfile',
                '.npmrc', '.yarnrc', '.env.example',
                'docker-compose.yml', 'Dockerfile',
                '.dockerignore', '.gitignore',
                'phpinfo.php', 'info.php', 'test.php',
                '.svn/', '.git/', '.hg/',
                '.env', '.git', '.htaccess', '.ssh',
                'config.js', 'settings.js', 'web.config',
                'credentials', 'secret', 'password',
                'deploy', 'backup', '.svn', '.hg',
            ],

            # Scan et Enumération
            'scanners': [
                'scanner', 'nikto', 'nmap', 'nuclei', 'zap', 
                'arachni', 'w3af', 'wpscan', 'sqlmap', 
                'dirbuster', 'gobuster', 'burp', 'acunetix',
                'nessus', 'whatweb', 'reconnaissance',
                'enum', 'hydra', 'brutus', 'skipfish', 
                'wapiti', 'whatweb', 'xspider', 'websecurify',
                'vega', 'owasp', 'metasploit',
            ],

            # Extensions Dangereuses
            'dangerous_extensions': [
                '.php', '.phtml', '.php3', '.php4', '.php5',
                '.asp', '.aspx', '.asa', '.cer', '.asax',
                '.jsp', '.jspx', '.jsw', '.jsv', '.jspf',
                '.exe', '.dll', '.so', '.sh', '.bat',
                '.cmd', '.pl', '.cgi', '.386', '.scr',
                '.msi', '.jar', '.py', '.rb', '.war',
            ],
        }

        # Combiner tous les patterns
        self.all_patterns = []
        for pattern_list in self.malicious_patterns.values():
            self.all_patterns.extend(pattern_list)

        # Configuration du tracking
        self.attempt_tracker = {}
        self.max_attempts = 5
        self.block_duration = 1800  # 30 minutes
        self.blocked_ips = {}
        self.suspicious_ips = {}
        self.last_cleanup = datetime.now().timestamp()
        self.suspicious_threshold = 5
        
    def get_client_ip(self, request):
        """Obtient l'IP réelle du client en tenant compte des proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_path_safe(self, path):
        """Vérifie si le chemin est dans la liste des chemins sûrs"""
        normalized_path = '/' + path.lstrip('/')
        return any(normalized_path.startswith(safe_path) for safe_path in self.safe_paths)

    def is_path_suspicious(self, path):
        """Vérifie si le chemin contient des patterns suspects"""
        if self.is_path_safe(path):
            return False
            
        path_lower = path.lower()
        
        # Vérification par catégorie de pattern malveillant
        for category, patterns in self.malicious_patterns.items():
            if any(pattern in path_lower for pattern in patterns):
                logger.warning(f"Pattern malveillant détecté [{category}]: {path}")
                return True
            
        # Vérification des caractères suspects
        suspicious_chars = re.compile(r'[<>\'"]|\.\.|%00|\\x|\\u')
        if suspicious_chars.search(path):
            logger.warning(f"Caractères suspects détectés: {path}")
            return True
            
        # Vérification de la longueur excessive
        if len(path) > 255:
            logger.warning(f"Chemin trop long: {len(path)} caractères")
            return True
            
        return False

    def analyze_request(self, request):
        """Analyse approfondie de la requête"""
        if self.is_path_safe(request.path):
            return 0, []

        suspicious_score = 0
        reasons = []

        # Vérification du User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) < 10:
            suspicious_score += 1
            reasons.append("User-Agent suspect")

        # Vérification des requêtes POST
        if request.method == 'POST':
            post_data = str(request.POST)
            for category, patterns in self.malicious_patterns.items():
                if any(pattern in post_data.lower() for pattern in patterns):
                    suspicious_score += 2
                    reasons.append(f"Contenu POST suspect ({category})")

        # Vérification des en-têtes
        for category, patterns in self.malicious_patterns.items():
            headers = str(request.headers).lower()
            if any(pattern in headers for pattern in patterns):
                suspicious_score += 1
                reasons.append(f"En-têtes suspects ({category})")

        return suspicious_score, reasons

    def get_funny_response(self, attack_type):
        """Génère une réponse humoristique basée sur le type d'attaque"""
        attack_responses = {
            "file_inclusion": "Les fichiers sont en quarantaine! 🔒",
            "sql_injection": "DROP TABLE hackers; -- Tentative supprimée 😎",
            "xss": "<script>alert('Nice Try!')</script> est bloqué ici 🛡️",
            "webshell": "Shell non disponible, essayez /bin/nope 🐚",
            "shell": "rm -rf /tentative_hack/* 🗑️",
            "bypass_attempts": "Contournement ? Plus comme détournement... vers Rick Astley 🎵",
            "sensitive_files": "Ces fichiers sont partis en vacances ! 🏖️",
            "scanners": "Scan terminé ! Résultat : Vous êtes bloqué 📊",
            "dangerous_extensions": "Extension refusée, essayez .nope 🚫",
        }
        return attack_responses.get(attack_type, random.choice(self.funny_messages))

    def detect_attack_type(self, path, request_data=None):
        """Détection du type d'attaque"""
        data_to_check = (path + str(request_data or '')).lower()
        
        for category, patterns in self.malicious_patterns.items():
            if any(pattern in data_to_check for pattern in patterns):
                return category

        return "unknown_attack"

    def log_attempt(self, request, ip, attack_type):
        """Log avec une touche d'humour"""
        log_data = SecurityLogFormatter.format_log_message(
            ip=ip,
            request=request,
            attack_type=attack_type,
            attempt_count=self.attempt_tracker.get(ip, 1)
        )
        
        # Ajout de l'analyse
        suspicious_score, reasons = self.analyze_request(request)
        log_data['🔍 Analyse'] = {
            'score': suspicious_score,
            'raisons': reasons,
            'type_attaque': attack_type
        }
        
        logger.warning(json.dumps(log_data, indent=2, ensure_ascii=False))

        # Log séparé pour les tentatives multiples
        if self.attempt_tracker.get(ip, 1) > 3:
            logger.error(
                f"🚨 ALERTE MULTIPLE: {ip} a fait {self.attempt_tracker[ip]} tentatives! "
                f"Type: {attack_type}, Score: {suspicious_score}"
            )

    def clean_old_records(self):
        """Nettoie les anciens enregistrements"""
        current_time = datetime.now().timestamp()
        if current_time - self.last_cleanup > 3600:
            self.blocked_ips = {
                ip: block_time 
                for ip, block_time in self.blocked_ips.items() 
                if current_time < block_time
            }
            self.attempt_tracker = {
                ip: count 
                for ip, count in self.attempt_tracker.items()
                if ip in self.blocked_ips
            }
            self.last_cleanup = current_time
            logger.info("🧹 Nettoyage des enregistrements effectué")

    def __call__(self, request):
        """Fonction principale du middleware"""
        self.clean_old_records()
        ip = self.get_client_ip(request)
        path = request.path.lstrip('/')

        # Vérification du chemin sûr
        if self.is_path_safe(path):
            return self.get_response(request)

        # Vérification du blocage
        if ip in self.blocked_ips:
            if datetime.now().timestamp() < self.blocked_ips[ip]:
                return HttpResponseForbidden(
                    "🎵 You've been blocked! Time to listen to some music... 🎵"
                )
            else:
                del self.blocked_ips[ip]

        suspicious_score, reasons = self.analyze_request(request)
        
        if self.is_path_suspicious(path) or suspicious_score >= self.suspicious_threshold:
            self.attempt_tracker[ip] = self.attempt_tracker.get(ip, 0) + 1
            attack_type = self.detect_attack_type(path, request.POST or request.GET)
            
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