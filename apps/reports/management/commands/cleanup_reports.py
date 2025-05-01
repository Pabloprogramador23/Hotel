import os
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Remove relatórios em media/reports/ com mais de 30 dias.'

    def handle(self, *args, **options):
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        if not os.path.exists(reports_dir):
            self.stdout.write(self.style.WARNING('Diretório de relatórios não encontrado.'))
            return
        now = time.time()
        cutoff = now - 30 * 24 * 60 * 60  # 30 dias em segundos
        removed = 0
        for filename in os.listdir(reports_dir):
            file_path = os.path.join(reports_dir, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    removed += 1
                    self.stdout.write(f'Removido: {filename}')
        if removed == 0:
            self.stdout.write(self.style.SUCCESS('Nenhum relatório antigo para remover.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'{removed} relatório(s) removido(s) com sucesso.'))
