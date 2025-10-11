"""Structure generator for automated project scaffolding.

This module generates project structures from templates including files,
directories, and initial content. Part of the Project Bootstrap Agent system.
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StructureGenerator:
    """Generates project structure from templates."""
    
    # Template definitions
    TEMPLATES = {
        'python': {
            'description': 'Python project with standard structure',
            'structure': {
                'src/': {
                    '__init__.py': '',
                    'main.py': '''#!/usr/bin/env python3
"""Main application entry point."""

def main():
    """Main function."""
    print("Hello from {project_name}!")

if __name__ == "__main__":
    main()
'''
                },
                'tests/': {
                    '__init__.py': '',
                    'test_main.py': '''"""Tests for main module."""
import pytest
from src.main import main

def test_main():
    """Test main function."""
    # Add your tests here
    pass
'''
                },
                'docs/': {
                    'API.md': '# API Documentation\n\nTODO: Add API documentation\n',
                    'ARCHITECTURE.md': '# Architecture\n\nTODO: Describe architecture\n'
                },
                'requirements.txt': 'pytest>=7.0.0\n',
                'setup.py': '''from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.8",
)
''',
                'README.md': '''# {project_name}

{description}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

## Development

```bash
pip install -r requirements.txt
pytest tests/
```

## License

MIT License - See LICENSE file for details
''',
                '.github/workflows/test.yml': '''name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/
'''
            }
        },
        'typescript': {
            'description': 'TypeScript project with Node.js',
            'structure': {
                'src/': {
                    'index.ts': '''/**
 * Main application entry point
 */

export function main(): void {
    console.log("Hello from {project_name}!");
}

if (require.main === module) {
    main();
}
'''
                },
                'tests/': {
                    'index.test.ts': '''import { main } from '../src/index';

describe('main', () => {
    it('should run without errors', () => {
        expect(() => main()).not.toThrow();
    });
});
'''
                },
                'package.json': '''{{
  "name": "{project_name}",
  "version": "0.1.0",
  "description": "{description}",
  "main": "dist/index.js",
  "scripts": {{
    "build": "tsc",
    "test": "jest",
    "start": "node dist/index.js"
  }},
  "devDependencies": {{
    "@types/node": "^20.0.0",
    "@types/jest": "^29.0.0",
    "jest": "^29.0.0",
    "ts-jest": "^29.0.0",
    "typescript": "^5.0.0"
  }},
  "license": "MIT"
}}
''',
                'tsconfig.json': '''{{
  "compilerOptions": {{
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true
  }},
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}}
''',
                'jest.config.js': '''module.exports = {{
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts']
}};
''',
                'README.md': '''# {project_name}

{description}

## Installation

```bash
npm install
```

## Usage

```bash
npm run build
npm start
```

## Development

```bash
npm run build
npm test
```

## License

MIT License - See LICENSE file for details
''',
                '.github/workflows/test.yml': '''name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run build
      - run: npm test
'''
            }
        },
        'go': {
            'description': 'Go project with modules',
            'structure': {
                'cmd/': {
                    'main.go': '''package main

import "fmt"

func main() {{
    fmt.Println("Hello from {project_name}!")
}}
'''
                },
                'pkg/': {},
                'go.mod': '''module github.com/{{owner}}/{project_name}

go 1.21
''',
                'README.md': '''# {project_name}

{description}

## Installation

```bash
go mod download
```

## Usage

```bash
go run cmd/main.go
```

## Build

```bash
go build -o {project_name} cmd/main.go
```

## License

MIT License - See LICENSE file for details
'''
            }
        }
    }
    
    def __init__(self):
        """Initialize structure generator."""
        logger.info("📁 Structure Generator initialized")
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List available project templates.
        
        Returns:
            List of template info dictionaries with 'name' and 'description'
        """
        return [
            {'name': name, 'description': template['description']}
            for name, template in self.TEMPLATES.items()
        ]
    
    def generate_structure(self,
                          template: str,
                          project_name: str,
                          description: str = "",
                          owner: str = "",
                          output_format: str = "files") -> Dict:
        """Generate project structure from template.
        
        Args:
            template: Template name (e.g., 'python', 'typescript')
            project_name: Project name for variable substitution
            description: Project description
            owner: Repository owner (for go.mod, etc.)
            output_format: 'files' (dict of paths/contents) or 'commands' (git commands)
            
        Returns:
            Dictionary with generated structure:
                - format: 'files' or 'commands'
                - data: Dict of file paths to contents OR list of git commands
                - file_count: Number of files generated
                
        Raises:
            ValueError: If template not found
        """
        if template not in self.TEMPLATES:
            available = ', '.join(self.TEMPLATES.keys())
            raise ValueError(f"Template '{template}' not found. Available: {available}")
        
        logger.info(f"🔨 Generating {template} project structure for '{project_name}'")
        
        template_data = self.TEMPLATES[template]
        structure = template_data['structure']
        
        # Variables for substitution
        variables = {
            'project_name': project_name,
            'description': description or f"A {template} project",
            'owner': owner or 'your-username',
            'year': datetime.now().year
        }
        
        files = {}
        self._process_structure(structure, '', files, variables)
        
        logger.info(f"✅ Generated {len(files)} files from {template} template")
        
        return {
            'format': output_format,
            'data': files,
            'file_count': len(files),
            'template': template
        }
    
    def _process_structure(self,
                          structure: Dict,
                          base_path: str,
                          output: Dict,
                          variables: Dict):
        """Recursively process structure definition.
        
        Args:
            structure: Template structure dictionary
            base_path: Current path prefix
            output: Output dictionary to populate
            variables: Variables for substitution
        """
        for name, content in structure.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                # Directory with nested items
                self._process_structure(content, path, output, variables)
            elif isinstance(content, str):
                # File with content
                processed_content = content.format(**variables)
                output[path] = processed_content
            else:
                # Empty file
                output[path] = ''
    
    def get_license_content(self, license_type: str = 'mit', owner: str = "", year: Optional[int] = None) -> str:
        """Generate license file content.
        
        Args:
            license_type: License type ('mit', 'apache-2.0', 'gpl-3.0')
            owner: Copyright holder name
            year: Copyright year (current year if None)
            
        Returns:
            License file content
        """
        if year is None:
            year = datetime.now().year
        
        licenses = {
            'mit': f'''MIT License

Copyright (c) {year} {owner}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''',
            'apache-2.0': f'''Apache License 2.0

Copyright {year} {owner}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
        }
        
        return licenses.get(license_type.lower(), licenses['mit'])
