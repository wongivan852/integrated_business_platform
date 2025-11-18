#!/usr/bin/env python3
"""
CSV Import Diagnostic Tool
Helps diagnose issues with CSV files before import
"""

import csv
import io
import re
from typing import Dict, List, Any

# Optional chardet import with fallback
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False

class CSVDiagnostic:
    """Diagnostic tool for CSV import issues"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
    
    def analyze_file(self, file_path_or_content: str, is_file_path: bool = True) -> Dict[str, Any]:
        """
        Comprehensive analysis of CSV file
        """
        try:
            if is_file_path:
                # Read file with encoding detection
                with open(file_path_or_content, 'rb') as f:
                    raw_data = f.read()
                
                # Detect encoding
                if HAS_CHARDET:
                    encoding_result = chardet.detect(raw_data)
                    encoding = encoding_result['encoding']
                    confidence = encoding_result['confidence']
                    self.info.append(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
                else:
                    # Fallback encoding detection
                    encoding = 'utf-8'  # Default assumption
                    self.info.append("Encoding detection: chardet not available, assuming UTF-8")
                
                # Try to decode
                try:
                    content = raw_data.decode(encoding)
                except UnicodeDecodeError:
                    # Fallback encodings
                    for fallback_encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            content = raw_data.decode(fallback_encoding)
                            self.warnings.append(f"Used fallback encoding: {fallback_encoding}")
                            encoding = fallback_encoding
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        self.issues.append("Could not decode file with any standard encoding")
                        return self._build_result()
            else:
                content = file_path_or_content
                encoding = 'provided_as_string'
            
            # Basic file analysis
            self.info.append(f"File size: {len(content)} characters")
            self.info.append(f"Number of lines: {content.count(chr(10)) + 1}")
            
            # Check for BOM
            if content.startswith('\ufeff'):
                self.info.append("UTF-8 BOM detected (will be handled)")
                content = content[1:]  # Remove BOM
            
            # Detect line endings
            if '\r\n' in content:
                line_ending = 'Windows (CRLF)'
            elif '\r' in content:
                line_ending = 'Mac (CR)'
            else:
                line_ending = 'Unix (LF)'
            self.info.append(f"Line endings: {line_ending}")
            
            # Analyze delimiters
            delimiter_analysis = self._analyze_delimiters(content)
            
            # Analyze structure
            structure_analysis = self._analyze_structure(content, delimiter_analysis['recommended_delimiter'])
            
            # Check for common issues
            issues_analysis = self._check_common_issues(content)
            
            # Field mapping analysis
            if structure_analysis.get('headers'):
                mapping_analysis = self._analyze_field_mapping(structure_analysis['headers'])
            else:
                mapping_analysis = {'field_mappings': {}, 'unmapped_headers': [], 'missing_mandatory': []}
            
            return self._build_result({
                'encoding': encoding,
                'delimiter_analysis': delimiter_analysis,
                'structure_analysis': structure_analysis,
                'issues_analysis': issues_analysis,
                'mapping_analysis': mapping_analysis,
                'content_sample': content[:500] + '...' if len(content) > 500 else content
            })
            
        except Exception as e:
            self.issues.append(f"Analysis failed: {str(e)}")
            return self._build_result()
    
    def _analyze_delimiters(self, content: str) -> Dict[str, Any]:
        """Analyze possible delimiters"""
        sample = content[:2048]  # First 2KB
        delimiters = {
            ',': 'Comma',
            ';': 'Semicolon', 
            '\t': 'Tab',
            '|': 'Pipe',
            '~': 'Tilde'
        }
        
        results = {}
        for delimiter, name in delimiters.items():
            count = sample.count(delimiter)
            if count > 0:
                # Test if this delimiter makes sense
                try:
                    reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
                    first_row = next(reader, [])
                    second_row = next(reader, [])
                    
                    if len(first_row) > 1 and len(second_row) > 1:
                        results[delimiter] = {
                            'name': name,
                            'count': count,
                            'first_row_fields': len(first_row),
                            'second_row_fields': len(second_row),
                            'consistent': len(first_row) == len(second_row)
                        }
                except:
                    pass
        
        # Recommend best delimiter
        if results:
            # Prefer consistent delimiters with reasonable field counts
            best_delimiter = max(results.keys(), 
                               key=lambda d: (results[d]['consistent'], results[d]['first_row_fields'], results[d]['count']))
        else:
            best_delimiter = ','
            self.warnings.append("No clear delimiter found, defaulting to comma")
        
        return {
            'available_delimiters': results,
            'recommended_delimiter': best_delimiter
        }
    
    def _analyze_structure(self, content: str, delimiter: str) -> Dict[str, Any]:
        """Analyze CSV structure"""
        try:
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            headers = reader.fieldnames
            
            if not headers:
                self.issues.append("No headers found in CSV")
                return {'headers': None, 'sample_rows': []}
            
            # Clean headers
            cleaned_headers = []
            for h in headers:
                if h is None:
                    self.warnings.append("Found None header - possible delimiter issue")
                    cleaned_headers.append(f"UNNAMED_COLUMN_{len(cleaned_headers)}")
                else:
                    cleaned_headers.append(str(h).strip())
            
            # Check for duplicate headers
            if len(cleaned_headers) != len(set(cleaned_headers)):
                duplicates = [h for h in cleaned_headers if cleaned_headers.count(h) > 1]
                self.warnings.append(f"Duplicate headers found: {duplicates}")
            
            # Sample rows
            sample_rows = []
            row_lengths = []
            
            for i, row in enumerate(reader):
                if i >= 5:  # First 5 rows
                    break
                
                # Check row consistency
                row_length = len([v for v in row.values() if v is not None])
                row_lengths.append(row_length)
                
                sample_rows.append(dict(row))
            
            # Check row consistency
            if row_lengths and len(set(row_lengths)) > 1:
                self.warnings.append(f"Inconsistent row lengths: {row_lengths}")
            
            return {
                'headers': cleaned_headers,
                'header_count': len(cleaned_headers),
                'sample_rows': sample_rows,
                'row_lengths': row_lengths
            }
            
        except Exception as e:
            self.issues.append(f"Structure analysis failed: {str(e)}")
            return {'headers': None, 'sample_rows': []}
    
    def _check_common_issues(self, content: str) -> Dict[str, Any]:
        """Check for common CSV issues"""
        issues_found = []
        
        # Check for mixed quotes
        if '"' in content and "'" in content:
            issues_found.append("Mixed quote types found - may cause parsing issues")
        
        # Check for unescaped quotes
        if re.search(r'(?<!"),".*".*".*,(?!")', content):
            issues_found.append("Possible unescaped quotes in data")
        
        # Check for very long lines (potential missing line breaks)
        lines = content.split('\n')
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        max_line_length = max(len(line) for line in lines) if lines else 0
        
        if max_line_length > avg_line_length * 10:
            issues_found.append(f"Extremely long line detected ({max_line_length} chars) - possible missing line breaks")
        
        # Check for null bytes
        if '\x00' in content:
            issues_found.append("Null bytes found - file may be corrupted")
        
        # Check for non-printable characters
        non_printable = [c for c in content[:1000] if ord(c) < 32 and c not in '\n\r\t']
        if non_printable:
            issues_found.append(f"Non-printable characters found: {[hex(ord(c)) for c in set(non_printable)]}")
        
        return {'issues': issues_found}
    
    def _analyze_field_mapping(self, headers: List[str]) -> Dict[str, Any]:
        """Analyze field mapping potential"""
        from .csv_import_handler import CSVImportHandler
        
        handler = CSVImportHandler()
        field_mapping, unmapped_headers = handler.analyze_headers(headers)
        missing_mandatory = handler.validate_mandatory_fields(field_mapping)
        
        return {
            'field_mappings': field_mapping,
            'unmapped_headers': unmapped_headers,
            'missing_mandatory': missing_mandatory,
            'mapping_confidence': len(field_mapping) / len(headers) if headers else 0
        }
    
    def _build_result(self, analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build final analysis result"""
        result = {
            'success': len(self.issues) == 0,
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info
        }
        
        if analysis:
            result.update(analysis)
        
        return result

def diagnose_csv_file(file_path: str) -> Dict[str, Any]:
    """Quick diagnostic function"""
    diagnostic = CSVDiagnostic()
    return diagnostic.analyze_file(file_path, is_file_path=True)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = diagnose_csv_file(sys.argv[1])
        print("=== CSV DIAGNOSTIC REPORT ===")
        print(f"Success: {result['success']}")
        
        if result.get('issues'):
            print("\n🚨 ISSUES:")
            for issue in result['issues']:
                print(f"  - {issue}")
        
        if result.get('warnings'):
            print("\n⚠️  WARNINGS:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        if result.get('info'):
            print("\nℹ️  INFO:")
            for info in result['info']:
                print(f"  - {info}")
        
        if result.get('delimiter_analysis'):
            print(f"\n📊 RECOMMENDED DELIMITER: {result['delimiter_analysis']['recommended_delimiter']}")
    else:
        print("Usage: python csv_diagnostic.py <csv_file_path>")