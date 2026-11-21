"""
FORMGUARD AI - Language Assistant Module
Multilingual support for English, Hindi, and Marathi.
"""

from typing import Dict, Optional


class LanguageAssistant:
    """
    Provides multilingual UI strings and translation support.
    Does NOT translate names, certificate numbers, or extracted identity fields.
    """

    # UI strings in all supported languages
    STRINGS = {
        "en": {
            "app_title": "FORMGUARD AI",
            "tagline": "Detect Before You Submit.",
            "welcome": "Welcome to FORMGUARD AI",
            "start_verification": "Start Application Verification",
            "upload_documents": "Upload Documents",
            "extract_data": "Extract Document Data",
            "run_verification": "Run Verification",
            "view_report": "View Report",
            "download_report": "Download Verification Report",
            "passed": "Passed",
            "warning": "Warning",
            "critical": "Critical",
            "manual_review": "Manual Review",
            "readiness": "Application Readiness",
            "no_issues": "No issues detected. All checks passed.",
            "disclaimer": (
                "This report provides AI-assisted document consistency and scheme-requirement checks. "
                "It is not an official government verification, eligibility decision, or guarantee of application approval."
            ),
            "select_scheme": "Select Government Scheme",
            "select_year": "Select Academic Year",
            "select_category": "Select Category",
            "required_docs": "Required Documents",
            "optional_docs": "Optional Documents",
            "missing_docs": "Missing Required Documents",
            "name_mismatch": "Name Mismatch Detected",
            "ask_question": "Ask a question about your verification...",
        },
        "hi": {
            "app_title": "FORMGUARD AI",
            "tagline": "जमा करने से पहले पता लगाएं।",
            "welcome": "FORMGUARD AI में आपका स्वागत है",
            "start_verification": "आवेदन सत्यापन शुरू करें",
            "upload_documents": "दस्तावेज़ अपलोड करें",
            "extract_data": "दस्तावेज़ डेटा निकालें",
            "run_verification": "सत्यापन चलाएं",
            "view_report": "रिपोर्ट देखें",
            "download_report": "सत्यापन रिपोर्ट डाउनलोड करें",
            "passed": "पास",
            "warning": "चेतावनी",
            "critical": "गंभीर",
            "manual_review": "मैन्युअल समीक्षा",
            "readiness": "आवेदन तैयारी",
            "no_issues": "कोई समस्या नहीं मिली। सभी जांच पास हुई।",
            "disclaimer": (
                "यह रिपोर्ट AI-सहायता प्राप्त दस्तावेज़ संगतता और योजना-आवश्यकता जांच प्रदान करती है। "
                "यह कोई आधिकारिक सरकारी सत्यापन, पात्रता निर्णय, या आवेदन स्वीकृति की गारंटी नहीं है।"
            ),
            "select_scheme": "सरकारी योजना चुनें",
            "select_year": "शैक्षणिक वर्ष चुनें",
            "select_category": "श्रेणी चुनें",
            "required_docs": "आवश्यक दस्तावेज़",
            "optional_docs": "वैकल्पिक दस्तावेज़",
            "missing_docs": "आवश्यक दस्तावेज़ गायब हैं",
            "name_mismatch": "नाम में विसंगति पाई गई",
            "ask_question": "अपने सत्यापन के बारे में प्रश्न पूछें...",
        },
        "mr": {
            "app_title": "FORMGUARD AI",
            "tagline": "सबमिट करण्यापूर्वी शोधा.",
            "welcome": "FORMGUARD AI मध्ये आपले स्वागत आहे",
            "start_verification": "अर्ज पडताळणी सुरू करा",
            "upload_documents": "कागदपत्रे अपलोड करा",
            "extract_data": "कागदपत्र डेटा काढा",
            "run_verification": "पडताळणी चालवा",
            "view_report": "अहवाल पहा",
            "download_report": "पडताळणी अहवाल डाउनलोड करा",
            "passed": "उत्तीर्ण",
            "warning": "इशारा",
            "critical": "गंभीर",
            "manual_review": "मॅन्युअल पुनरावलोकन",
            "readiness": "अर्ज तयारी",
            "no_issues": "कोणतीही समस्या आढळली नाही. सर्व तपासण्या उत्तीर्ण.",
            "disclaimer": (
                "हा अहवाल AI-सहाय्यित कागदपत्र सुसंगतता आणि योजना-आवश्यकता तपासण्या प्रदान करतो. "
                "हे कोणतेही अधिकृत सरकारी पडताळणी, पात्रता निर्णय किंवा अर्ज मंजुरीची हमी नाही."
            ),
            "select_scheme": "सरकारी योजना निवडा",
            "select_year": "शैक्षणिक वर्ष निवडा",
            "select_category": "प्रवर्ग निवडा",
            "required_docs": "आवश्यक कागदपत्रे",
            "optional_docs": "ऐच्छिक कागदपत्रे",
            "missing_docs": "आवश्यक कागदपत्रे गहाळ आहेत",
            "name_mismatch": "नावातील विसंगती आढळली",
            "ask_question": "तुमच्या पडताळणीबद्दल प्रश्न विचारा...",
        },
    }

    @staticmethod
    def get_string(key: str, language: str = "en") -> str:
        """Get a UI string in the specified language."""
        lang_strings = LanguageAssistant.STRINGS.get(language, LanguageAssistant.STRINGS["en"])
        return lang_strings.get(key, LanguageAssistant.STRINGS["en"].get(key, key))

    @staticmethod
    def get_all_strings(language: str = "en") -> Dict[str, str]:
        """Get all UI strings for a language."""
        return LanguageAssistant.STRINGS.get(language, LanguageAssistant.STRINGS["en"])

    @staticmethod
    def get_severity_label(severity: str, language: str = "en") -> str:
        """Get localized severity label."""
        mapping = {
            "en": {"PASS": "Pass", "WARNING": "Warning", "CRITICAL": "Critical", "MANUAL_REVIEW": "Manual Review"},
            "hi": {"PASS": "पास", "WARNING": "चेतावनी", "CRITICAL": "गंभीर", "MANUAL_REVIEW": "मैन्युअल समीक्षा"},
            "mr": {"PASS": "उत्तीर्ण", "WARNING": "इशारा", "CRITICAL": "गंभीर", "MANUAL_REVIEW": "मॅन्युअल पुनरावलोकन"},
        }
        lang_map = mapping.get(language, mapping["en"])
        return lang_map.get(severity, severity)
