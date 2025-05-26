# Contract Risk Assessment - Redundancy Cleanup Guide

This document outlines the redundant files that can be safely removed after confirming that the improved versions are working correctly.

## Flask Application Files

### API and Routes
- `Flask/app/views/api.py` - Replaced by `Flask/app/views/imp_api.py`
- `Flask/app/views/upt_api.py` - Replaced by `Flask/app/views/imp_api.py`
- `Flask/app/views/upt_dashboard.py` - Replaced by `Flask/app/views/imp_dashboard.py`

### Models and Database
- `Flask/app/models.py` - Replaced by `Flask/app/imp_models.py`
- `Flask/app/upt_models.py` - Replaced by `Flask/app/imp_models.py`

### Celery Configuration
- `Flask/app/upt_celery_app.py` - Replaced by `Flask/app/imp_celery_app.py`
- `Flask/app/upt_celery_config.py` - Replaced by `Flask/app/imp_celery_config.py`
- `Flask/app/upt_tasks.py` - Replaced by `Flask/app/imp_tasks.py`

### Templates
- `Flask/app/templates/base.html` - Replaced by `Flask/app/templates/imp_base.html`
- `Flask/app/templates/dashboard/contracts.html` - Replaced by `Flask/app/templates/dashboard/imp_contracts.html`

### Static Assets
- `Flask/app/static/js/dashboard.js` - Replaced by `Flask/app/static/js/imp_dashboard.js`
- `Flask/app/static/js/upt_dashboard.js` - Replaced by `Flask/app/static/js/imp_dashboard.js`
- `Flask/app/static/css/dashboard.css` - Replaced by `Flask/app/static/css/imp_dashboard.css`
- `Flask/app/static/css/upt_dashboard.css` - Replaced by `Flask/app/static/css/imp_dashboard.css`

## Contract Analysis Components

### Pipeline Components
- `src/contract_analysis/pipeline.py` - Replaced by `src/contract_analysis/imp_pipeline.py`
- `src/contract_analysis/upt_pipeline.py` - Replaced by `src/contract_analysis/imp_pipeline.py`

### Risk Scoring
- `src/contract_analysis/risk_scorer.py` - Replaced by `src/contract_analysis/imp_risk_scorer.py`
- `src/contract_analysis/upt_risk_scorer.py` - Replaced by `src/contract_analysis/imp_risk_scorer.py`

### Tools Integration
- `src/contract_analysis/tools_integration.py` - Replaced by `src/contract_analysis/imp_tools_integration.py`
- `src/contract_analysis/upt_tools_integration.py` - Replaced by `src/contract_analysis/imp_tools_integration.py`

## Legacy Directories

The following directories contain older versions of components that have been consolidated into the improved versions:

- `COMPOSE/` - All files in this directory have been analyzed and merged into improved versions
- `DEV/` - Development versions have been incorporated into the improved components

## Removal Process

1. First ensure that all automated tests pass with the improved components
2. Make a backup of the entire project before deletion
3. Remove files one category at a time, verifying functionality after each step
4. Keep the legacy directories until the end of the cleanup process for reference

## Note

Before removing any files, make sure the application runs correctly with the improved components. Run through the following test scenarios:

1. User login and authentication
2. Contract upload (both legal and smart contracts)
3. Contract analysis requests
4. Dashboard rendering and contract list display
5. Contract analysis results display
