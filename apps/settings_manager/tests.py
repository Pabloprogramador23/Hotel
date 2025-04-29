import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from apps.settings_manager.models import SystemSetting  # Importação corrigida

@pytest.mark.django_db
class TestSystemSettingModel:
    def test_create_setting(self):
        """Teste de criação de uma configuração"""
        setting = SystemSetting.objects.create(
            key="test_key",
            value="test_value",
            description="Test description"
        )
        assert setting.key == "test_key"
        assert setting.value == "test_value"
        assert setting.description == "Test description"
        assert str(setting) == "test_key: test_value"

    def test_unique_key_constraint(self):
        """Teste de restrição de chave única"""
        SystemSetting.objects.create(key="unique_key", value="value1")
        
        with pytest.raises(Exception):  # Deve lançar exceção por chave duplicada
            SystemSetting.objects.create(key="unique_key", value="value2")

@pytest.mark.django_db
class TestSystemSettingViews:
    @pytest.fixture
    def setup_user_with_permissions(self):
        """Fixture para criar usuário com permissões necessárias"""
        user = User.objects.create_user(username='testuser', password='password')
        content_type = ContentType.objects.get_for_model(SystemSetting)
        
        # Adicionar todas as permissões para o modelo
        permissions = Permission.objects.filter(content_type=content_type)
        for perm in permissions:
            user.user_permissions.add(perm)
        
        return user
    
    @pytest.fixture
    def setup_sample_settings(self):
        """Fixture para criar algumas configurações de teste"""
        settings = [
            SystemSetting.objects.create(key=f"key_{i}", value=f"value_{i}", 
                                         description=f"description_{i}")
            for i in range(3)
        ]
        return settings
    
    def test_settings_list_view(self, client, setup_user_with_permissions, setup_sample_settings):
        """Teste da view de listagem de configurações"""
        client.login(username='testuser', password='password')
        response = client.get(reverse('settings_manager:list'))
        
        assert response.status_code == 200
        for setting in setup_sample_settings:
            assert setting.key in str(response.content)
            assert setting.value in str(response.content)
    
    def test_settings_create_view(self, client, setup_user_with_permissions):
        """Teste da view de criação de configurações"""
        client.login(username='testuser', password='password')
        
        # Teste GET
        response = client.get(reverse('settings_manager:create'))
        assert response.status_code == 200
        
        # Teste POST
        response = client.post(
            reverse('settings_manager:create'),
            {'key': 'new_key', 'value': 'new_value', 'description': 'New description'}
        )
        
        assert response.status_code == 302  # Redirecionamento após sucesso
        assert SystemSetting.objects.filter(key='new_key').exists()
        
    def test_settings_edit_view(self, client, setup_user_with_permissions, setup_sample_settings):
        """Teste da view de edição de configurações"""
        client.login(username='testuser', password='password')
        setting = setup_sample_settings[0]
        
        # Teste GET
        response = client.get(reverse('settings_manager:edit', args=[setting.id]))
        assert response.status_code == 200
        
        # Teste POST
        response = client.post(
            reverse('settings_manager:edit', args=[setting.id]),
            {'key': setting.key, 'value': 'updated_value', 'description': 'Updated description'}
        )
        
        assert response.status_code == 302  # Redirecionamento após sucesso
        setting.refresh_from_db()
        assert setting.value == 'updated_value'
        assert setting.description == 'Updated description'
    
    def test_settings_delete_view(self, client, setup_user_with_permissions, setup_sample_settings):
        """Teste da view de exclusão de configurações"""
        client.login(username='testuser', password='password')
        setting = setup_sample_settings[0]
        setting_id = setting.id
        
        # Teste GET
        response = client.get(reverse('settings_manager:delete', args=[setting_id]))
        assert response.status_code == 200
        
        # Teste POST
        response = client.post(reverse('settings_manager:delete', args=[setting_id]))
        assert response.status_code == 302  # Redirecionamento após sucesso
        assert not SystemSetting.objects.filter(id=setting_id).exists()
