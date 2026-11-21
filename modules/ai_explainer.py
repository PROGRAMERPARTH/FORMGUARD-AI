"""
FORMGUARD AI - AI Explanation Engine
LLM-powered explanations grounded in verification results and RAG.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.rag_pipeline import RAGPipeline


class AIExplainer:
    """
    AI-powered explanation engine using Gemini API.
    Falls back to template-based explanations when API is unavailable.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = None
        self.rag = RAGPipeline()
        self._init_model()

    def _init_model(self):
        """Initialize the Gemini model."""
        if not self.api_key:
            print("[AI] No GEMINI_API_KEY set. Using template-based explanations.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            print("[AI] Gemini model initialized.")
        except ImportError:
            print("[AI] google-generativeai not installed. Using template-based explanations.")
        except Exception as e:
            print(f"[AI] Gemini init error: {e}. Using template-based explanations.")

    def explain_check(self, check: Dict, language: str = "en") -> Dict:
        """
        Generate an explanation for a verification check.
        Returns dict with 'explanation', 'recommended_steps', 'sources'.
        """
        severity = check.get("severity", "PASS")
        check_name = check.get("check_name", "")
        reason = check.get("reason", "")
        field = check.get("field_checked", "")
        values = check.get("extracted_values", {})
        action = check.get("recommended_action", "")

        # Query RAG for relevant context
        rag_query = f"{check_name} {reason} {field}"
        rag_results = self.rag.query(rag_query, scheme_id="mahadbt_postmatric", top_k=3)
        rag_context = "\n".join([r["text"] for r in rag_results])
        sources = [r.get("source", "") + " - " + r.get("title", "") for r in rag_results if r.get("source")]

        if self.model:
            return self._llm_explain(check, rag_context, sources, language)
        else:
            return self._template_explain(check, rag_results, sources, language)

    def answer_question(self, question: str, context: str, language: str = "en") -> Dict:
        """
        Answer a user question using context and RAG.
        Returns dict with 'answer', 'sources', 'is_grounded'.
        """
        # Query RAG
        rag_results = self.rag.query(question, scheme_id="mahadbt_postmatric", top_k=5)
        rag_context = "\n".join([r["text"] for r in rag_results])
        sources = [r.get("source", "") + " - " + r.get("title", "") for r in rag_results if r.get("source")]

        if self.model:
            return self._llm_answer(question, context, rag_context, sources, language)
        else:
            return self._template_answer(question, context, rag_results, sources, language)

    def _llm_explain(self, check: Dict, rag_context: str, sources: List[str], language: str) -> Dict:
        """Generate explanation using LLM."""
        lang_instruction = self._get_language_instruction(language)

        prompt = f"""You are FORMGUARD AI, an assistant helping Indian students with government scholarship applications.

{lang_instruction}

A verification check has the following result:
- Check Name: {check.get('check_name', '')}
- Severity: {check.get('severity', '')}
- Field Checked: {check.get('field_checked', '')}
- Reason: {check.get('reason', '')}
- Extracted Values: {check.get('extracted_values', {})}
- Recommended Action: {check.get('recommended_action', '')}

Relevant official guidelines:
{rag_context if rag_context else 'No specific guidelines found for this issue.'}

Please provide:
1. A clear, simple explanation of this issue (2-3 sentences)
2. Specific steps the student should take to resolve it (numbered list)

Important rules:
- Base your answer on the official guidelines provided above
- Do not fabricate government policies or requirements
- Do not guarantee application approval
- If the guidelines don't cover this specific issue, say that manual verification with official sources is recommended
- Keep the explanation simple and actionable"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text

            # Parse response
            parts = text.split("\n")
            explanation = []
            steps = []
            in_steps = False

            for line in parts:
                line = line.strip()
                if not line:
                    continue
                if any(line.startswith(f"{i}.") or line.startswith(f"{i})") for i in range(1, 10)):
                    in_steps = True
                    steps.append(line)
                elif in_steps:
                    steps.append(line)
                else:
                    explanation.append(line)

            return {
                "explanation": " ".join(explanation) if explanation else text,
                "recommended_steps": steps if steps else [check.get("recommended_action", "Review the document.")],
                "sources": sources,
                "is_grounded": bool(rag_context),
            }

        except Exception as e:
            print(f"[AI] LLM explain error: {e}")
            return self._template_explain(check, [], sources, language)

    def _llm_answer(self, question: str, context: str, rag_context: str, sources: List[str], language: str) -> Dict:
        """Answer using LLM with RAG context."""
        lang_instruction = self._get_language_instruction(language)

        prompt = f"""You are FORMGUARD AI, an assistant helping Indian students with government scholarship applications (MahaDBT portal, Maharashtra).

{lang_instruction}

The student's verification context:
{context[:3000]}

Relevant official guidelines:
{rag_context if rag_context else 'No specific guidelines retrieved for this query.'}

Student's question: {question}

Important rules:
- Answer based on the verification results and official guidelines provided
- Clearly distinguish between: extracted facts, potential issues, official requirements, and general recommendations
- Do not fabricate government policies
- Do not guarantee application approval
- If you don't have enough information, say so and recommend checking the official MahaDBT portal
- Keep the answer clear and actionable
- Do not alter names, certificate numbers, or identity fields when translating"""

        try:
            response = self.model.generate_content(prompt)
            return {
                "answer": response.text,
                "sources": sources,
                "is_grounded": bool(rag_context),
            }
        except Exception as e:
            print(f"[AI] LLM answer error: {e}")
            return self._template_answer(question, context, [], sources, language)

    def _template_explain(self, check: Dict, rag_results: List[Dict], sources: List[str], language: str) -> Dict:
        """Generate a template-based explanation when LLM is unavailable."""
        severity = check.get("severity", "PASS")
        reason = check.get("reason", "")
        action = check.get("recommended_action", "")

        if language == "hi":
            explanations = {
                "CRITICAL": f"⚠️ यह एक गंभीर समस्या है जो आपके आवेदन को रोक सकती है: {reason}",
                "WARNING": f"⚠️ यह एक संभावित समस्या है जिसकी समीक्षा आवश्यक है: {reason}",
                "MANUAL_REVIEW": f"🔍 इस विवरण की मैन्युअल जांच आवश्यक है: {reason}",
                "PASS": f"✅ यह जांच सफलतापूर्वक पास हुई: {reason}",
            }
            rag_prefix = "\n\n📚 आधिकारिक महाडीबीटी दिशानिर्देश अनुसार: "
        elif language == "mr":
            explanations = {
                "CRITICAL": f"⚠️ ही एक गंभीर समस्या आहे ज्यामुळे तुमचा अर्ज प्रलंबित राहू शकतो: {reason}",
                "WARNING": f"⚠️ ही एक संभाव्य समस्या आहे ज्याची पडताळणी आवश्यक आहे: {reason}",
                "MANUAL_REVIEW": f"🔍 या तपशीलाचे मॅन्युअल पुनरावलोकन आवश्यक आहे: {reason}",
                "PASS": f"✅ ही तपासणी यशस्वीरित्या पूर्ण झाली: {reason}",
            }
            rag_prefix = "\n\n📚 अधिकृत महाडीबीटी मार्गदर्शक तत्त्वांनुसार: "
        else:
            explanations = {
                "CRITICAL": f"⚠️ This is a critical issue that may prevent your application from being processed: {reason}",
                "WARNING": f"⚠️ This is a potential issue that you should review: {reason}",
                "MANUAL_REVIEW": f"🔍 This item requires your manual review: {reason}",
                "PASS": f"✅ This check has passed: {reason}",
            }
            rag_prefix = "\n\n📚 According to official MahaDBT guidelines: "

        explanation = explanations.get(severity, reason)

        # Add RAG context if available
        if rag_results:
            explanation += rag_prefix + rag_results[0].get("text", "")[:250]

        steps = []
        if action:
            steps.append(action)
        if severity in ("CRITICAL", "WARNING"):
            if language == "hi":
                steps.append("निकाले गए विवरणों की तुलना अपने मूल दस्तावेजों से करें।")
                steps.append("यदि त्रुटि वास्तविक है, तो जारीकर्ता कार्यालय से सही दस्तावेज प्राप्त करें।")
            elif language == "mr":
                steps.append("काढून घेतलेल्या तपशीलांची आपल्या मूळ कागदपत्रांशी तुलना करा.")
                steps.append("त्रुटी खरी असल्यास, संबंधित प्राधिकरणाकडून दुरुस्त कागदपत्र मिळवा.")
            else:
                steps.append("Review the extracted values and compare with your original documents.")
                steps.append("If there is a genuine error, get the document corrected and re-upload.")
        if severity == "MANUAL_REVIEW":
            if language == "hi":
                steps.append("निकाले गए पाठ की सटीकता की मैन्युअल समीक्षा करें।")
            elif language == "mr":
                steps.append("काढलेल्या मजकुराची अचूकता मॅन्युअली तपासा.")
            else:
                steps.append("Review the extracted text manually for accuracy.")

        return {
            "explanation": explanation,
            "recommended_steps": steps,
            "sources": sources,
            "is_grounded": bool(rag_results),
        }

    def _template_answer(self, question: str, context: str, rag_results: List[Dict], sources: List[str], language: str) -> Dict:
        """Generate template-based answer when LLM is unavailable."""
        question_lower = question.lower()

        if language == "hi":
            if any(word in question_lower for word in ["name", "mismatch", "नाम"]):
                answer = (
                    "दस्तावेजों में नाम की विसंगति छात्रवृत्ति आवेदनों में एक आम समस्या है। "
                    "यह सुनिश्चित करें कि सभी प्रमाण पत्रों पर आपका नाम बिल्कुल एक जैसा लिखा हो। "
                    "यदि नाम में वास्तविक अंतर है, तो नाम सुधार शपथ पत्र (Affidavit) या राजपत्र (Gazette) अधिसूचना की आवश्यकता हो सकती है।"
                )
            elif any(word in question_lower for word in ["missing", "document", "दस्तावेज", "कागजात"]):
                answer = (
                    "सत्यापन परिणामों के अनुसार, कुछ आवश्यक दस्तावेज अभी अपलोड नहीं किए गए हैं। "
                    "कृपया आवश्यक दस्तावेजों की पूरी सूची देखने के लिए अपलोड पृष्ठ की जांच करें। "
                    "प्रत्येक योजना के लिए निर्धारित सभी अनिवार्य दस्तावेज अपलोड करना आवश्यक है।"
                )
            elif any(word in question_lower for word in ["income", "limit", "आय"]):
                answer = (
                    "आय पात्रता योजना और श्रेणी के अनुसार भिन्न होती है। महाडीबीटी पोस्ट-मैट्रिक छात्रवृत्ति के लिए, "
                    "सामान्यतः SC/ST और OBC श्रेणियों के लिए वार्षिक पारिवारिक आय सीमा ₹2,50,000 (2.5 लाख) है। "
                    "कृपया महाडीबीटी पोर्टल पर अपनी विशिष्ट योजना के लिए सटीक सीमा अवश्य सत्यापित करें।"
                )
            else:
                answer = (
                    "मैं आपके सत्यापन परिणामों से संबंधित प्रश्नों में सहायता कर सकता हूँ। "
                    "विशिष्ट समस्याओं और सिफारिशों के लिए कृपया विस्तृत सत्यापन परिणाम देखें। "
                    "आधिकारिक महाडीबीटी पोर्टल (https://mahadbt.maharashtra.gov.in/) या अपने कॉलेज के नोडल अधिकारी से संपर्क करें।"
                )
            rag_header = "\n\n📚 **आधिकारिक दिशानिर्देशों से:** "
        elif language == "mr":
            if any(word in question_lower for word in ["name", "mismatch", "नाव"]):
                answer = (
                    "कागदपत्रांमध्ये नावाची तफावत ही शिष्यवृत्ती अर्जांमध्ये वारंवार आढळणारी समस्या आहे. "
                    "सर्व प्रमाणपत्रांवर आपले नाव तंतोतंत जुळत असल्याची खात्री करा. "
                    "नावात कायदेशीर बदल असल्यास, राजपत्र (Gazette) किंवा प्रतिज्ञापत्र (Affidavit) आवश्यक असू शकते."
                )
            elif any(word in question_lower for word in ["missing", "document", "कागदपत्रे"]):
                answer = (
                    "पडताळणीच्या निष्कर्षांनुसार, काही अनिवार्य कागदपत्रे अद्याप अपलोड केलेली नाहीत. "
                    "कृपया आवश्यक कागदपत्रांची यादी पाहण्यासाठी अपलोड पृष्ठावर जा. "
                    "अर्ज यशस्वीपणे मंजूर होण्यासाठी सर्व अनिवार्य कागदपत्रे आवश्यक आहेत."
                )
            elif any(word in question_lower for word in ["income", "limit", "उत्पन्न"]):
                answer = (
                    "उत्पन्नाची मर्यादा योजना आणि प्रवर्गानुसार ठरवली जाते. महाडीबीटी पोस्ट-मॅट्रिक शिष्यवृत्तीसाठी, "
                    "बहुतांश SC/ST आणि OBC प्रवर्गांसाठी वार्षिक कौटुंबिक उत्पन्न मर्यादा ₹२,५०,००० (२.५ लाख) आहे. "
                    "कृपया अधिक माहितीसाठी महाडीबीटी पोर्टलवरील नियमावली तपासा."
                )
            else:
                answer = (
                    "मी आपल्या अर्ज पडताळणीविषयीच्या प्रश्नांमध्ये मदत करू शकतो. "
                    "तपशीलवार माहितीसाठी कृपया वरील पडताळणी निष्कर्ष तपासा. "
                    "अधिकृत माहितीसाठी महाडीबीटी पोर्टल (https://mahadbt.maharashtra.gov.in/) किंवा कॉलेजच्या नोडल अधिकाऱ्यांशी संपर्क साधा."
                )
            rag_header = "\n\n📚 **अधिकृत मार्गदर्शक तत्त्वांनुसार:** "
        else:
            # Pattern-match common questions
            if any(word in question_lower for word in ["name", "mismatch", "different name"]):
                answer = (
                    "Name mismatches across documents are a common issue in scholarship applications. "
                    "Ensure your name is spelled exactly the same on all certificates. If there is a "
                    "genuine difference (e.g., due to marriage or legal name change), you may need to "
                    "provide a name correction affidavit or gazette notification."
                )
            elif any(word in question_lower for word in ["missing", "document", "required"]):
                answer = (
                    "Based on your verification results, some required documents may be missing. "
                    "Please check the upload page for the complete list of required documents. "
                    "Each scheme has specific document requirements that must be met for the application to be processed."
                )
            elif any(word in question_lower for word in ["income", "limit", "eligibility"]):
                answer = (
                    "Income eligibility varies by scheme and category. For most MahaDBT post-matric scholarships, "
                    "the annual family income limit is around ₹2,50,000 (2.5 Lakhs) for SC/ST categories. "
                    "Please verify the exact limit for your specific scheme on the MahaDBT portal."
                )
            elif any(word in question_lower for word in ["correct", "fix", "how to"]):
                answer = (
                    "To correct issues in your application: "
                    "1. Identify the specific issue from the verification results. "
                    "2. Get the original document corrected from the issuing authority if needed. "
                    "3. Re-upload the corrected document. "
                    "4. Run verification again to confirm the fix. "
                    "For name corrections, you may need a gazette notification or affidavit."
                )
            elif any(word in question_lower for word in ["academic year", "year", "session"]):
                answer = (
                    "The academic year on your documents must match the year you are applying for. "
                    "Your college bonafide should show the current academic year, while your marksheet "
                    "should be from the previous academic session. Mismatched years are a common "
                    "reason for application returns."
                )
            else:
                answer = (
                    "I can help with questions about your verification results. Based on the checks performed, "
                    "please review the detailed verification results for specific issues and recommendations. "
                    "For scheme-specific questions, I recommend checking the official MahaDBT portal at "
                    "https://mahadbt.maharashtra.gov.in/ or contacting your college's scholarship nodal officer."
                )
            rag_header = "\n\n📚 **From official guidelines:** "

        # Append RAG context if available
        if rag_results:
            answer += rag_header + rag_results[0].get("text", "")[:300]

        return {
            "answer": answer,
            "sources": sources,
            "is_grounded": bool(rag_results),
        }

    def _get_language_instruction(self, language: str) -> str:
        """Get language instruction for the LLM."""
        instructions = {
            "en": "Respond in English.",
            "hi": "Respond in Hindi (हिन्दी). Keep official terms, names, certificate numbers, and document names in their original form.",
            "mr": "Respond in Marathi (मराठी). Keep official terms, names, certificate numbers, and document names in their original form.",
        }
        return instructions.get(language, "Respond in English.")
