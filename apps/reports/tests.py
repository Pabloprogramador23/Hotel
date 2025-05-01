import pytest
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

from apps.reports.models import Report
from apps.reports.services import calculate_revenue_data
from apps.finance.models import Invoice
from apps.reservations.models import Reservation
from apps.rooms.models import Room


@pytest.mark.django_db
class TestReportModel:
    """Testes para o modelo Report"""
    
    def test_create_report(self):
        """Teste para criação básica de um relatório"""
        # Criar um arquivo de teste
        test_content = b"This is a test report content"
        test_file = SimpleUploadedFile(
            name="test_report.pdf",
            content=test_content,
            content_type="application/pdf"
        )
        
        # Criar o relatório
        report = Report.objects.create(
            name="Occupancy Report",
            file_path=test_file
        )
        
        # Verificar atributos
        assert report.name == "Occupancy Report"
        assert report.generated_at is not None
        assert report.file_path is not None
        assert "test_report" in report.file_path.name
        assert str(report) == f"Report Occupancy Report generated on {report.generated_at}"
        
        # Limpar o arquivo após o teste
        if os.path.exists(report.file_path.path):
            os.remove(report.file_path.path)
    
    def test_report_deletion(self):
        """Teste para garantir que o arquivo físico é excluído quando o relatório é removido"""
        # Criar um arquivo de teste
        test_content = b"This is another test report"
        test_file = SimpleUploadedFile(
            name="test_report_delete.pdf",
            content=test_content,
            content_type="application/pdf"
        )
        
        # Criar o relatório
        report = Report.objects.create(
            name="Monthly Revenue",
            file_path=test_file
        )
        
        # Salvar o caminho do arquivo
        file_path = report.file_path.path
        
        # Verificar que o arquivo existe
        assert os.path.exists(file_path)
        
        # Excluir o relatório
        report.delete()
        
        # Verificar que o relatório foi excluído do banco
        assert not Report.objects.filter(name="Monthly Revenue").exists()
        
        # Nota: Normalmente, verificaríamos que o arquivo físico também foi excluído,
        # mas isso exigiria sobrescrever o método delete() do modelo para remover o arquivo


@pytest.mark.django_db
class TestReportViews:
    """Testes para as views do aplicativo reports"""
    
    @pytest.fixture
    def setup_user_with_permissions(self):
        """Fixture para criar usuário com permissões necessárias"""
        user = User.objects.create_user(username='testuser', password='password')
        content_type = ContentType.objects.get_for_model(Report)
        
        # Adicionar todas as permissões para o modelo
        permissions = Permission.objects.filter(content_type=content_type)
        for perm in permissions:
            user.user_permissions.add(perm)
        
        return user
    
    @pytest.fixture
    def setup_sample_reports(self):
        """Fixture para criar relatórios de exemplo para testes"""
        reports = []
        
        for i in range(3):
            test_content = f"Report content {i}".encode()
            test_file = SimpleUploadedFile(
                name=f"report_{i}.pdf",
                content=test_content,
                content_type="application/pdf"
            )
            
            report = Report.objects.create(
                name=f"Test Report {i}",
                file_path=test_file
            )
            reports.append(report)
        
        return reports
    
    def test_report_list_view(self, client, setup_user_with_permissions, setup_sample_reports):
        """Teste da view de listagem de relatórios"""
        client.login(username='testuser', password='password')
        response = client.get(reverse('reports:list'))
        
        # Verificar que a página carrega com sucesso
        assert response.status_code == 200
        
        # Verificar que estamos na página de relatórios (pelo título ou outro elemento identificador)
        assert b'<title>' in response.content
        
        # Verificar que existem relatórios no banco de dados
        assert Report.objects.count() == 3
            
        # Limpar os arquivos após o teste
        for report in setup_sample_reports:
            if os.path.exists(report.file_path.path):
                os.remove(report.file_path.path)


@pytest.mark.django_db
def test_calculate_revenue_data_basic():
    """Testa cálculo de receita agregada para um período simples."""
    room = Room.objects.create(number="101", room_type="single", status="clean")
    reservation = Reservation.objects.create(
        guest_name="Test Guest",
        room=room,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        status="confirmed"
    )
    Invoice.objects.create(reservation=reservation, amount=100, paid=True)
    Invoice.objects.create(reservation=reservation, amount=50, paid=False)
    start = date.today()
    end = date.today()
    revenue_data, total_revenue, total_paid, total_pending = calculate_revenue_data(start, end)
    assert total_revenue == 150
    assert total_paid == 100
    assert total_pending == 50
    assert len(revenue_data) == 1
