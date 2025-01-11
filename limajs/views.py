from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control

@method_decorator(cache_control(public=True, max_age=3600), name='dispatch')
class GalaxyHomeView(TemplateView):
    """
    Vue principale qui affiche l'animation de la galaxie.
    Le cache est défini pour 1 heure pour optimiser les performances.
    """
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Limajs Motors'
        return context