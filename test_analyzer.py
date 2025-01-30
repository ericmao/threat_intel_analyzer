import unittest
from unittest.mock import patch, Mock, mock_open
import os
from analyzer import analyze_threat_intel_pdf, format_results

class TestThreatIntelAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.sample_results = [
            {
                "threat_actor": "APT29",
                "malware_name": "SUNBURST",
                "attack_vector": "Supply Chain Attack",
                "indicators": "example.com, 192.168.1.1",
                "targeted_sectors": "Government, Technology",
                "severity": "High"
            },
            {
                "threat_actor": "FIN7",
                "malware_name": "CARBANAK",
                "attack_vector": "Phishing",
                "indicators": "malicious.com",
                "targeted_sectors": "Financial",
                "severity": "Medium"
            }
        ]

    @patch('analyzer.PyPDFLoader')
    @patch('analyzer.CharacterTextSplitter')
    @patch('analyzer.ChatOpenAI')
    @patch('analyzer.create_extraction_chain')
    def test_analyze_threat_intel_pdf_success(self, mock_chain, mock_chat, mock_splitter, mock_loader):
        """Test successful PDF analysis"""
        # Mock the PDF loader
        mock_page = Mock()
        mock_page.page_content = "Sample threat intel content"
        mock_loader.return_value.load_and_split.return_value = [mock_page]
        
        # Mock the text splitter
        mock_splitter.return_value.split_documents.return_value = [mock_page]
        
        # Mock the extraction chain
        mock_chain.return_value.run.return_value = [self.sample_results[0]]
        
        result = analyze_threat_intel_pdf("sample.pdf")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["threat_actor"], "APT29")
        self.assertEqual(result[0]["malware_name"], "SUNBURST")

    @patch('analyzer.PyPDFLoader')
    @patch('analyzer.CharacterTextSplitter')
    @patch('analyzer.ChatOpenAI')
    @patch('analyzer.create_extraction_chain')
    def test_analyze_threat_intel_pdf_error(self, mock_chain, mock_chat, mock_splitter, mock_loader):
        """Test error handling in PDF analysis"""
        # Mock the PDF loader to raise an exception
        mock_loader.return_value.load_and_split.side_effect = Exception("PDF loading error")
        
        with self.assertRaises(Exception):
            analyze_threat_intel_pdf("sample.pdf")

    def test_format_results_success(self):
        """Test successful formatting of results"""
        formatted_output = format_results(self.sample_results)
        
        # Check if the formatted output contains expected information
        self.assertIn("Threat Intelligence Analysis Summary", formatted_output)
        self.assertIn("Finding 1:", formatted_output)
        self.assertIn("APT29", formatted_output)
        self.assertIn("SUNBURST", formatted_output)
        self.assertIn("Finding 2:", formatted_output)
        self.assertIn("FIN7", formatted_output)
        self.assertIn("CARBANAK", formatted_output)

    def test_format_results_empty(self):
        """Test formatting with empty results"""
        formatted_output = format_results([])
        self.assertIn("Threat Intelligence Analysis Summary", formatted_output)
        self.assertNotIn("Finding 1:", formatted_output)

    def test_format_results_partial_data(self):
        """Test formatting with partial data"""
        partial_results = [
            {
                "threat_actor": "APT29",
                "malware_name": "SUNBURST",
                "attack_vector": "Supply Chain Attack",
                # Missing optional fields
            }
        ]
        
        formatted_output = format_results(partial_results)
        self.assertIn("APT29", formatted_output)
        self.assertIn("SUNBURST", formatted_output)
        self.assertNotIn("severity", formatted_output.lower())

if __name__ == '__main__':
    unittest.main()
