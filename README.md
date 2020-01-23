# Open edX Proversity additional reports plugin.

## Description

This plugin contains additional reports for the Open edX platform.

## API versions.

### API V1 configuration.

You must add a new backend configuration to enable a new report data API endpoint.

    settings.OPR_SUPPORTED_REPORTS_BACKENDS = {
        'generate_<my_report_name>': {
            'backend': '<module_python_path>:<backend_class>',
            'max_results_per_page': <max_number_of_data_results_per_page>,
            'other_custom_report_setting': ...
        },
        'generate_<my_other_report_name>': {
            'backend': 'backend': '<module_python_path>:<backend_class>',
            'max_results_per_page': <max_number_of_data_results_per_page>,
            'other_custom_report_setting': ...
        }...
    }
