#!/usr/bin/env python3
"""
Project Structure Reorganizer

This script reorganizes the Contract_Eval project into a more maintainable structure.
It handles file movements, updates import paths, and creates necessary configuration files.
"""

import os
import shutil
import logging
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import re
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('restructure.log')
    ]
)
logger = logging.getLogger(__name__)

class ProjectRestructurer:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.temp_dir = self.project_root / '.restructure_temp'
        self.backup_dir = self.project_root / 'backup_before_restructure'
        
        # Define the new project structure
        self.new_structure = {
            'backend/': {
                'app/': {
                    'api/': {
                        'v1/': {
                            'endpoints/': [
                                'analysis.py',
                                'auth.py',
                                'results.py'
                            ]
                        }
                    },
                    'core/': {
                        'analysis/': [
                            'detectors/',
                            'services.py',
                            'utils.py'
                        ],
                        'models/': [
                            'schemas.py',
                            'database.py'
                        ],
                        'services/': [
                            'analysis_service.py',
                            'auth_service.py'
                        ]
                    },
                    'db/': {
                        'migrations/': [],
                        'session.py': None
                    },
                    'utils/': [
                        'file_utils.py',
                        'logging_utils.py'
                    ],
                    'config.py': None,
                    '__init__.py': None
                },
                'tests/': {
                    'unit/': [],
                    'integration/': [],
                    'conftest.py': None
                },
                'alembic/': [
                    'env.py',
                    'script.py.mako'
                ],
                'main.py': None,
                'requirements/': {
                    'base.txt': None,
                    'dev.txt': None,
                    'prod.txt': None
                }
            },
            'frontend/': {
                'public/': [
                    'index.html',
                    'favicon.ico'
                ],
                'src/': {
                    'components/': {
                        'common/': [
                            'Button.tsx',
                            'Card.tsx',
                            'Header.tsx'
                        ],
                        'analysis/': [
                            'ContractUploader.tsx',
                            'ResultsViewer.tsx'
                        ]
                    },
                    'features/': {
                        'auth/': [
                            'components/LoginForm.tsx',
                            'hooks/useAuth.ts'
                        ],
                        'dashboard/': [
                            'components/DashboardView.tsx'
                        ]
                    },
                    'services/': [
                        'api.ts',
                        'auth.ts'
                    ],
                    'App.tsx': None,
                    'main.tsx': None
                },
                'vite.config.ts': None
            },
            'docs/': {
                'api/': [
                    'rest.md',
                    'graphql.md'
                ],
                'development/': [
                    'setup.md',
                    'testing.md'
                ]
            },
            'scripts/': [
                'setup.py',
                'deploy.py'
            ],
            'docker/': [
                'Dockerfile.backend',
                'Dockerfile.frontend',
                'docker-compose.yml'
            ],
            '.github/': {
                'workflows/': [
                    'ci.yml',
                    'cd.yml'
                ]
            },
            'pyproject.toml': None,
            'README.md': None,
            '.env.example': None
        }

        # Map old file locations to new ones
        self.file_mappings = self._generate_file_mappings()
        
        # Track moved files for import updates
        self.moved_files: Dict[Path, Path] = {}
        
        # Track files that need import updates
        self.files_to_update: Set[Path] = set()

    def _generate_file_mappings(self) -> Dict[str, str]:
        """Generate mappings from old file paths to new ones."""
        return {
            # Backend mappings
            'backend/main.py': 'backend/app/main.py',
            'backend/requirements.txt': 'backend/requirements/base.txt',
            'backend/core/analysis/utils.py': 'backend/app/core/analysis/services.py',
            
            # Frontend mappings - adjust based on actual frontend structure
            'frontend/package.json': 'frontend/package.json',
            'frontend/tsconfig.json': 'frontend/tsconfig.json',
            'frontend/vite.config.ts': 'frontend/vite.config.ts',
            'frontend/src/App.tsx': 'frontend/src/App.tsx',
            
            # Documentation
            'README.md': 'README.md',
            'CONTRIBUTING.md': 'docs/development/CONTRIBUTING.md',
            'LICENSE': 'LICENSE',
            
            # Add more mappings as needed
        }

    def _create_directory(self, path: Path) -> None:
        """Create a directory if it doesn't exist."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    def _copy_file(self, src: Path, dest: Path) -> None:
        """Copy a file from src to dest, creating parent directories if needed."""
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            self.moved_files[src] = dest
            logger.debug(f"Copied {src} to {dest}")
        except Exception as e:
            logger.error(f"Failed to copy {src} to {dest}: {e}")
            raise

    def _create_structure(self, base_path: Path, structure: dict) -> None:
        """Create the directory and file structure."""
        for name, content in structure.items():
            path = base_path / name.rstrip('/')
            
            if isinstance(content, dict):
                # It's a directory with more content
                self._create_directory(path)
                self._create_structure(path, content)
            elif isinstance(content, list):
                # It's a directory with listed files/subdirs
                self._create_directory(path)
                for item in content:
                    if item.endswith('/'):
                        # It's a subdirectory
                        subdir = path / item.rstrip('/')
                        self._create_directory(subdir)
                    else:
                        # It's a file
                        file_path = path / item
                        file_path.touch()
                        logger.debug(f"Created empty file: {file_path}")
            elif content is None:
                # It's a file
                path.touch()
                logger.debug(f"Created empty file: {path}")

    def _move_files(self) -> None:
        """Move files according to the mappings."""
        for src_relative, dest_relative in self.file_mappings.items():
            src = self.project_root / src_relative
            dest = self.project_root / dest_relative
            
            if not src.exists():
                logger.warning(f"Source file not found: {src}")
                continue
                
            # Create parent directory if it doesn't exist
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            try:
                if src.is_file():
                    shutil.move(str(src), str(dest))
                    self.moved_files[src] = dest
                    logger.info(f"Moved {src} to {dest}")
                    self.files_to_update.add(dest)
                elif src.is_dir():
                    shutil.copytree(str(src), str(dest), dirs_exist_ok=True)
                    shutil.rmtree(str(src))
                    logger.info(f"Moved directory {src} to {dest}")
                    # Add all Python/TypeScript files in the directory to update list
                    for ext in ('*.py', '*.ts', '*.tsx'):
                        for file in dest.rglob(ext):
                            self.files_to_update.add(file)
            except Exception as e:
                logger.error(f"Error moving {src} to {dest}: {e}")

    def _update_imports(self) -> None:
        """Update import paths in all relevant files."""
        for file_path in self.files_to_update:
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated = False
                
                # Update Python imports
                if file_path.suffix == '.py':
                    for old_import, new_import in self._get_python_import_mappings().items():
                        pattern = re.compile(rf'(\bfrom\s+){re.escape(old_import)}(\s+import\b|\s*,\s*)')
                        new_content, count = pattern.subn(
                            rf'\1{new_import}\2', content
                        )
                        if count > 0:
                            updated = True
                            content = new_content
                
                # Update TypeScript/JavaScript imports
                elif file_path.suffix in ('.ts', '.tsx', '.js', '.jsx'):
                    for old_import, new_import in self._get_typescript_import_mappings().items():
                        pattern = re.compile(rf'(\bfrom\s+[\'"])(\.*\/?{re.escape(old_import)})([\'"])')
                        new_content, count = pattern.subn(
                            rf'\1{new_import}\3', content
                        )
                        if count > 0:
                            updated = True
                            content = new_content
                
                if updated:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Updated imports in {file_path}")
                    
            except Exception as e:
                logger.error(f"Error updating imports in {file_path}: {e}")

    def _get_python_import_mappings(self) -> Dict[str, str]:
        """Generate Python import mappings based on the new structure."""
        return {
            'backend.core.analysis.utils': 'backend.app.core.analysis.services',
            'backend.core': 'backend.app.core',
            'backend.models': 'backend.app.models',
            'backend.api': 'backend.app.api.v1',
            # Add more mappings as needed
        }

    def _get_typescript_import_mappings(self) -> Dict[str, str]:
        """Generate TypeScript import mappings based on the new structure."""
        return {
            # Add TypeScript import mappings here
            # Example:
            # '../../components': '@/components',
            # '../../services': '@/services',
        }

    def _create_config_files(self) -> None:
        """Create essential configuration files with default content."""
        # Create pyproject.toml
        pyproject_path = self.project_root / 'pyproject.toml'
        if not pyproject_path.exists():
            pyproject_content = """[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "contract_eval"
version = "0.1.0"
description = "Smart Contract Security Analysis Tool"
readme = "README.md"
requires-python = ">=3.8"
authors = [
    { name = "Your Name", email = "your.email@example.com" },
]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "black>=22.3.0",
    "isort>=5.0.0",
    "mypy>=0.910",
    "pytest-cov>=2.0",
]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'
"""
            with open(pyproject_path, 'w') as f:
                f.write(pyproject_content)
            logger.info(f"Created {pyproject_path}")

        # Create .env.example
        env_example_path = self.project_root / '.env.example'
        if not env_example_path.exists():
            env_content = """# Backend Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db

# Frontend Configuration
VITE_API_URL=http://localhost:8000/api/v1
"""
            with open(env_example_path, 'w') as f:
                f.write(env_content)
            logger.info(f"Created {env_example_path}")

    def _create_backend_structure(self) -> None:
        """Create backend-specific structure and files."""
        backend_dir = self.project_root / 'backend' / 'app'
        
        # Create __init__.py files
        for dirpath, _, _ in os.walk(backend_dir):
            if dirpath.endswith('__pycache__'):
                continue
            init_file = Path(dirpath) / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                logger.debug(f"Created {init_file}")

    def run(self) -> None:
        """Run the restructuring process."""
        logger.info("Starting project restructuring...")
        
        try:
            # Create backup
            logger.info("Creating backup...")
            self._create_directory(self.backup_dir)
            shutil.copytree(
                str(self.project_root),
                str(self.backup_dir / 'original'),
                ignore=shutil.ignore_patterns(
                    '*.pyc', '__pycache__', 'node_modules', '.git', 'venv', '.venv',
                    '*.log', '*.sqlite', '*.db', '*.sqlite3', '*.db-journal'
                )
            )
            
            # Create new structure
            logger.info("Creating new project structure...")
            self._create_structure(self.project_root, self.new_structure)
            
            # Move files to new locations
            logger.info("Moving files to new locations...")
            self._move_files()
            
            # Update import paths
            logger.info("Updating import paths...")
            self._update_imports()
            
            # Create configuration files
            logger.info("Creating configuration files...")
            self._create_config_files()
            
            # Set up backend structure
            logger.info("Setting up backend structure...")
            self._create_backend_structure()
            
            logger.info("Restructuring completed successfully!")
            logger.info(f"Backup is available at: {self.backup_dir}")
            logger.info("Please review the changes and test the application.")
            
        except Exception as e:
            logger.critical(f"Error during restructuring: {e}")
            logger.info(f"Check the log file for details: {self.project_root}/restructure.log")
            raise

def main() -> None:
    """Main entry point for the script."""
    try:
        project_root = Path.cwd()
        restructurer = ProjectRestructurer(project_root)
        restructurer.run()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()