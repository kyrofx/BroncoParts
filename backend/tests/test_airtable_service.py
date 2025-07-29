import pytest
from unittest.mock import patch, MagicMock, Mock
import json
from app.services.airtable_service import (
    get_airtable_table, 
    sync_part_to_airtable,
    add_option_to_airtable_subsystem_field,
    get_airtable_select_options,
    add_option_via_typecast,
    AIRTABLE_NAME,
    AIRTABLE_SUBTEAM,
    AIRTABLE_SUBSYSTEM,
    AIRTABLE_MANUFACTURING_QUANTITY,
    AIRTABLE_STATUS,
    AIRTABLE_MACHINE,
    AIRTABLE_RAW_MATERIAL,
    AIRTABLE_POST_PROCESS,
    AIRTABLE_NOTES
)


class TestAirtableService:
    
    @pytest.mark.unit
    @patch('app.services.airtable_service.Table')
    def test_get_airtable_table_success(self, mock_table_class, app):
        """Test successful Airtable table initialization"""
        mock_table = MagicMock()
        mock_table_class.return_value = mock_table
        
        with app.app_context():
            table = get_airtable_table()
            
            assert table is not None
            mock_table_class.assert_called_once_with(
                'test-airtable-key',
                'test-base-id', 
                'test-table-id'
            )

    @pytest.mark.unit
    def test_get_airtable_table_missing_config(self, app):
        """Test Airtable table initialization with missing config"""
        # Override config to have missing values
        app.config['AIRTABLE_API_KEY'] = None
        
        with app.app_context():
            table = get_airtable_table()
            assert table is None

    @pytest.mark.unit
    def test_get_airtable_table_placeholder_key(self, app):
        """Test Airtable table initialization with placeholder API key"""
        app.config['AIRTABLE_API_KEY'] = 'YOUR_AIRTABLE_API_KEY'
        
        with app.app_context():
            table = get_airtable_table()
            assert table is None

    @pytest.mark.unit
    @patch('app.services.airtable_service.Table')
    def test_get_airtable_table_initialization_error(self, mock_table_class, app):
        """Test Airtable table initialization with exception"""
        mock_table_class.side_effect = Exception("Connection failed")
        
        with app.app_context():
            table = get_airtable_table()
            assert table is None

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    def test_get_airtable_select_options_success(self, mock_get_table, app):
        """Test successful retrieval of Airtable select options"""
        # Mock table and schema
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock schema response
        mock_field = MagicMock()
        mock_field.name = 'Test Field'
        mock_field.type = 'singleSelect'
        
        # Mock choices
        mock_choice1 = MagicMock()
        mock_choice1.name = 'Option 1'
        mock_choice2 = MagicMock()
        mock_choice2.name = 'Option 2'
        
        mock_field.options.choices = [mock_choice1, mock_choice2]
        
        mock_schema = MagicMock()
        mock_schema.fields = [mock_field]
        mock_table.schema.return_value = mock_schema
        
        with app.app_context():
            options = get_airtable_select_options(mock_table, 'Test Field')
            
            assert options == ['Option 1', 'Option 2']

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    def test_get_airtable_select_options_not_select_field(self, mock_get_table, app):
        """Test retrieval of options for non-select field"""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock schema with text field
        mock_field = MagicMock()
        mock_field.name = 'Text Field'
        mock_field.type = 'singleLineText'
        
        mock_schema = MagicMock()
        mock_schema.fields = [mock_field]
        mock_table.schema.return_value = mock_schema
        
        with app.app_context():
            options = get_airtable_select_options(mock_table, 'Text Field')
            assert options == []

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    def test_get_airtable_select_options_field_not_found(self, mock_get_table, app):
        """Test retrieval of options for non-existent field"""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock schema with no matching field
        mock_schema = MagicMock()
        mock_schema.fields = []
        mock_table.schema.return_value = mock_schema
        
        with app.app_context():
            options = get_airtable_select_options(mock_table, 'Nonexistent Field')
            assert options == []

    @pytest.mark.unit
    @patch('app.services.airtable_service.requests.post')
    def test_add_option_via_typecast_success(self, mock_post, app):
        """Test successful addition of option via typecast method"""
        # Mock successful creation response
        mock_create_response = MagicMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {
            'records': [{'id': 'rec123456'}]
        }
        mock_create_response.raise_for_status.return_value = None
        
        # Mock successful deletion response
        mock_delete_response = MagicMock()
        mock_delete_response.status_code = 200
        mock_delete_response.raise_for_status.return_value = None
        
        mock_post.side_effect = [mock_create_response]
        
        with patch('app.services.airtable_service.requests.delete') as mock_delete:
            mock_delete.return_value = mock_delete_response
            
            with app.app_context():
                result = add_option_via_typecast('New Option', 'Test Field')
                
                assert result is True
                mock_post.assert_called_once()
                mock_delete.assert_called_once()

    @pytest.mark.unit
    @patch('app.services.airtable_service.requests.post')
    def test_add_option_via_typecast_creation_fails(self, mock_post, app):
        """Test typecast method when record creation fails"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_post.return_value = mock_response
        
        with app.app_context():
            result = add_option_via_typecast('New Option', 'Test Field')
            assert result is False

    @pytest.mark.unit
    def test_add_option_via_typecast_missing_config(self, app):
        """Test typecast method with missing configuration"""
        app.config['AIRTABLE_API_KEY'] = None
        
        with app.app_context():
            result = add_option_via_typecast('New Option', 'Test Field')
            assert result is False

    @pytest.mark.unit
    def test_add_option_via_typecast_empty_option(self, app):
        """Test typecast method with empty option value"""
        with app.app_context():
            result = add_option_via_typecast('', 'Test Field')
            assert result is False
            
            result = add_option_via_typecast('   ', 'Test Field')
            assert result is False

    @pytest.mark.unit
    @patch('app.services.airtable_service.add_option_via_typecast')
    @patch('app.services.airtable_service.get_airtable_table')
    def test_add_option_to_airtable_subsystem_field_typecast_success(self, mock_get_table, mock_typecast, app):
        """Test successful subsystem field option addition via typecast"""
        mock_typecast.return_value = True
        
        with app.app_context():
            result = add_option_to_airtable_subsystem_field('New Subsystem')
            
            assert result is True
            mock_typecast.assert_called_once_with('New Subsystem', AIRTABLE_SUBSYSTEM)

    @pytest.mark.unit
    @patch('app.services.airtable_service.add_option_via_typecast')
    @patch('app.services.airtable_service._update_airtable_field_choices')
    @patch('app.services.airtable_service.get_airtable_table')
    def test_add_option_to_airtable_subsystem_field_fallback(self, mock_get_table, mock_update_choices, mock_typecast, app):
        """Test subsystem field option addition fallback to metadata API"""
        mock_typecast.return_value = False  # Typecast fails
        mock_update_choices.return_value = True  # Metadata API succeeds
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        with app.app_context():
            result = add_option_to_airtable_subsystem_field('New Subsystem')
            
            assert result is True
            mock_typecast.assert_called_once()
            mock_update_choices.assert_called_once()

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_sync_part_to_airtable_success(self, mock_get_options, mock_get_table, app, sample_part):
        """Test successful part synchronization to Airtable"""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock select options
        mock_get_options.side_effect = lambda table, field: {
            AIRTABLE_SUBTEAM: ['Test Assembly'],
            AIRTABLE_SUBSYSTEM: ['Test Assembly'], 
            AIRTABLE_STATUS: ['in design'],
            AIRTABLE_MACHINE: ['Test Machine'],
            AIRTABLE_POST_PROCESS: ['Test Post Process']
        }.get(field, [])
        
        # Mock successful record creation
        mock_table.create.return_value = {'id': 'rec123456', 'fields': {}}
        
        with app.app_context():
            result = sync_part_to_airtable(sample_part)
            
            assert result is not None
            assert result['id'] == 'rec123456'
            mock_table.create.assert_called_once()
            
            # Verify the data passed to create
            call_args = mock_table.create.call_args[0][0]
            assert AIRTABLE_NAME in call_args
            assert AIRTABLE_MANUFACTURING_QUANTITY in call_args
            assert call_args[AIRTABLE_MANUFACTURING_QUANTITY] == sample_part.quantity

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    def test_sync_part_to_airtable_no_table(self, mock_get_table, app, sample_part):
        """Test part sync when Airtable table is not available"""
        mock_get_table.return_value = None
        
        with app.app_context():
            result = sync_part_to_airtable(sample_part)
            assert result is None

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_sync_part_to_airtable_create_fails(self, mock_get_options, mock_get_table, app, sample_part):
        """Test part sync when record creation fails"""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_get_options.return_value = []
        
        # Mock creation failure
        mock_table.create.side_effect = Exception("Creation failed")
        
        with app.app_context():
            result = sync_part_to_airtable(sample_part)
            assert result is None

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_sync_part_invalid_select_options(self, mock_get_options, mock_get_table, app, sample_part):
        """Test part sync with invalid select field options"""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock select options that don't include our part's values
        mock_get_options.side_effect = lambda table, field: {
            AIRTABLE_STATUS: ['different status'],  # Part has 'in design'
            AIRTABLE_MACHINE: ['different machine']  # Part has 'Test Machine'
        }.get(field, [])
        
        mock_table.create.return_value = {'id': 'rec123456'}
        
        with app.app_context():
            result = sync_part_to_airtable(sample_part)
            
            # Should still succeed but with omitted invalid fields
            assert result is not None
            call_args = mock_table.create.call_args[0][0]
            
            # Invalid fields should be omitted
            assert AIRTABLE_STATUS not in call_args or call_args[AIRTABLE_STATUS] == sample_part.status
            assert AIRTABLE_MACHINE not in call_args or call_args[AIRTABLE_MACHINE] == sample_part.machine.name

    @pytest.mark.unit
    def test_sync_part_data_mapping(self, app, sample_part):
        """Test that part data is correctly mapped to Airtable fields"""
        with patch('app.services.airtable_service.get_airtable_table') as mock_get_table:
            mock_table = MagicMock()
            mock_get_table.return_value = mock_table
            
            with patch('app.services.airtable_service.get_airtable_select_options') as mock_get_options:
                # Mock all fields as valid
                mock_get_options.return_value = ['valid_option']
                
                mock_table.create.return_value = {'id': 'rec123456'}
                
                with app.app_context():
                    # Update sample part with known values
                    sample_part.machine.name = 'valid_option'
                    sample_part.status = 'valid_option'
                    
                    result = sync_part_to_airtable(sample_part)
                    
                    assert result is not None
                    call_args = mock_table.create.call_args[0][0]
                    
                    # Verify field mappings
                    expected_name = f"{sample_part.part_number}: {sample_part.name}"
                    assert call_args[AIRTABLE_NAME] == expected_name
                    assert call_args[AIRTABLE_MANUFACTURING_QUANTITY] == sample_part.quantity
                    assert call_args[AIRTABLE_RAW_MATERIAL] == sample_part.raw_material
                    assert call_args[AIRTABLE_NOTES] == sample_part.description

    @pytest.mark.unit
    @patch('app.services.airtable_service.get_airtable_table')
    @patch('app.services.airtable_service.get_airtable_select_options')
    def test_sync_part_with_post_processes(self, mock_get_options, mock_get_table, app, sample_part):
        """Test part sync with multiple post processes"""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock post process options
        mock_get_options.side_effect = lambda table, field: {
            AIRTABLE_POST_PROCESS: ['Test Post Process', 'Another Process']
        }.get(field, [])
        
        mock_table.create.return_value = {'id': 'rec123456'}
        
        with app.app_context():
            # Ensure part has post processes
            assert len(sample_part.post_processes) > 0
            
            result = sync_part_to_airtable(sample_part)
            
            assert result is not None
            call_args = mock_table.create.call_args[0][0]
            
            # Should include valid post processes
            assert AIRTABLE_POST_PROCESS in call_args
            assert isinstance(call_args[AIRTABLE_POST_PROCESS], list)
            assert 'Test Post Process' in call_args[AIRTABLE_POST_PROCESS]


class TestAirtableIntegration:
    
    @pytest.mark.integration
    @patch('app.services.airtable_service.requests.patch')
    @patch('app.services.airtable_service.get_airtable_table')
    def test_update_airtable_field_choices_success(self, mock_get_table, mock_patch, app):
        """Test successful field choice update via metadata API"""
        from app.services.airtable_service import _update_airtable_field_choices
        
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock schema response
        mock_field = MagicMock()
        mock_field.id = 'fld123456'
        mock_field.name = 'Test Field'
        mock_field.type = 'singleSelect'
        
        # Mock existing choices
        mock_choice = MagicMock()
        mock_choice.name = 'Existing Option'
        mock_choice.id = 'sel123'
        mock_choice.color = 'blue'
        mock_field.options.choices = [mock_choice]
        
        mock_schema = MagicMock()
        mock_schema.fields = [mock_field]
        mock_table.schema.return_value = mock_schema
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'fld123456'}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response
        
        with app.app_context():
            result = _update_airtable_field_choices(mock_table, 'Test Field', 'New Option')
            
            assert result is True
            mock_patch.assert_called_once()

    @pytest.mark.integration  
    @patch('app.services.airtable_service.requests.patch')
    @patch('app.services.airtable_service.get_airtable_table')
    def test_update_airtable_field_choices_too_many_options(self, mock_get_table, mock_patch, app):
        """Test field choice update when approaching choice limit"""
        from app.services.airtable_service import _update_airtable_field_choices
        
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        
        # Mock schema with many existing choices
        mock_field = MagicMock()
        mock_field.id = 'fld123456'
        mock_field.name = 'Test Field'
        mock_field.type = 'singleSelect'
        
        # Create 46 mock choices (above the 45 limit)
        mock_choices = []
        for i in range(46):
            mock_choice = MagicMock()
            mock_choice.name = f'Option {i}'
            mock_choices.append(mock_choice)
        
        mock_field.options.choices = mock_choices
        
        mock_schema = MagicMock()
        mock_schema.fields = [mock_field]
        mock_table.schema.return_value = mock_schema
        
        with app.app_context():
            result = _update_airtable_field_choices(mock_table, 'Test Field', 'New Option')
            
            # Should fail due to too many existing choices
            assert result is False
            mock_patch.assert_not_called()

    @pytest.mark.integration
    @patch('app.services.airtable_service.get_airtable_table')
    def test_airtable_service_error_handling(self, mock_get_table, app):
        """Test error handling in Airtable service functions"""
        mock_get_table.side_effect = Exception("Network error")
        
        with app.app_context():
            # All functions should handle errors gracefully
            table = get_airtable_table()
            assert table is None
            
            result = add_option_to_airtable_subsystem_field('Test Option')
            assert result is False