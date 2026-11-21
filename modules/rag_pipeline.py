"""
FORMGUARD AI - RAG Pipeline Module
Retrieval-Augmented Generation for government scheme knowledge.
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))


class RAGPipeline:
    """
    RAG pipeline for retrieving official government scheme information.
    Uses FAISS for vector search and Sentence Transformers for embeddings.
    """

    def __init__(self):
        self.embeddings_model = None
        self.vector_store = None
        self.documents = []
        self.is_initialized = False
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load the built-in scheme knowledge base."""
        # Built-in MahaDBT knowledge (from official sources)
        self.knowledge_base = self._get_mahadbt_knowledge()

        # Try to initialize FAISS
        try:
            self._init_vector_store()
        except Exception as e:
            print(f"[RAG] Vector store initialization skipped: {e}")
            # RAG will work in fallback keyword-search mode

    def _init_vector_store(self):
        """Initialize the FAISS vector store with embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np

            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.embeddings_model = SentenceTransformer(model_name)

            # Create embeddings for all knowledge chunks
            texts = [chunk["text"] for chunk in self.knowledge_base]
            if texts:
                embeddings = self.embeddings_model.encode(texts, convert_to_numpy=True)

                try:
                    import faiss
                    dimension = embeddings.shape[1]
                    self.vector_store = faiss.IndexFlatIP(dimension)
                    # Normalize for cosine similarity
                    faiss.normalize_L2(embeddings)
                    self.vector_store.add(embeddings)
                    self.is_initialized = True
                    print(f"[RAG] Initialized with {len(texts)} chunks in FAISS")
                except ImportError:
                    # Fallback: use numpy for similarity search
                    self._numpy_embeddings = embeddings
                    self.is_initialized = True
                    print(f"[RAG] Initialized with {len(texts)} chunks (numpy fallback)")

        except ImportError as e:
            print(f"[RAG] Sentence Transformers not available: {e}")
        except Exception as e:
            print(f"[RAG] Vector store init error: {e}")

    def query(self, question: str, scheme_id: str = "", top_k: int = 5) -> List[Dict]:
        """
        Query the knowledge base.
        Returns list of relevant chunks with metadata.
        """
        if self.is_initialized and self.embeddings_model:
            return self._vector_search(question, scheme_id, top_k)
        else:
            return self._keyword_search(question, scheme_id, top_k)

    def _vector_search(self, question: str, scheme_id: str, top_k: int) -> List[Dict]:
        """Search using FAISS vector similarity."""
        try:
            import numpy as np

            query_embedding = self.embeddings_model.encode([question], convert_to_numpy=True)

            if self.vector_store is not None:
                import faiss
                faiss.normalize_L2(query_embedding)
                scores, indices = self.vector_store.search(query_embedding, min(top_k * 2, len(self.knowledge_base)))

                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(self.knowledge_base) and score > 0.2:
                        chunk = self.knowledge_base[idx].copy()
                        chunk["relevance_score"] = float(score)
                        if not scheme_id or chunk.get("scheme_id", "") == scheme_id or chunk.get("scheme_id", "") == "general":
                            results.append(chunk)
                return results[:top_k]

            elif hasattr(self, '_numpy_embeddings'):
                # Numpy fallback
                from numpy.linalg import norm
                query_norm = query_embedding / norm(query_embedding)
                emb_norm = self._numpy_embeddings / norm(self._numpy_embeddings, axis=1, keepdims=True)
                scores = (emb_norm @ query_norm.T).flatten()

                top_indices = scores.argsort()[-top_k * 2:][::-1]
                results = []
                for idx in top_indices:
                    if scores[idx] > 0.2:
                        chunk = self.knowledge_base[idx].copy()
                        chunk["relevance_score"] = float(scores[idx])
                        if not scheme_id or chunk.get("scheme_id", "") == scheme_id or chunk.get("scheme_id", "") == "general":
                            results.append(chunk)
                return results[:top_k]

        except Exception as e:
            print(f"[RAG] Vector search error: {e}")

        return self._keyword_search(question, scheme_id, top_k)

    def _keyword_search(self, question: str, scheme_id: str, top_k: int) -> List[Dict]:
        """Fallback keyword-based search."""
        question_lower = question.lower()
        keywords = set(question_lower.split())
        # Remove common words
        stop_words = {"what", "is", "the", "how", "can", "i", "my", "a", "an", "for", "to", "do", "in", "of", "and"}
        keywords -= stop_words

        scored = []
        for chunk in self.knowledge_base:
            if scheme_id and chunk.get("scheme_id", "") not in (scheme_id, "general"):
                continue

            text_lower = chunk["text"].lower()
            score = sum(1 for kw in keywords if kw in text_lower)
            # Boost if title matches
            title_lower = chunk.get("title", "").lower()
            score += sum(2 for kw in keywords if kw in title_lower)

            if score > 0:
                chunk_copy = chunk.copy()
                chunk_copy["relevance_score"] = score / max(len(keywords), 1)
                scored.append(chunk_copy)

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_k]

    def get_scheme_requirements(self, scheme_id: str) -> List[Dict]:
        """Get all requirement chunks for a specific scheme."""
        return [
            chunk for chunk in self.knowledge_base
            if chunk.get("scheme_id") == scheme_id and chunk.get("category") == "requirement"
        ]

    def _get_mahadbt_knowledge(self) -> List[Dict]:
        """
        Built-in knowledge base derived from official MahaDBT sources.
        Source: https://mahadbt.maharashtra.gov.in/
        """
        return [
            # ── General MahaDBT Information ──
            {
                "text": "MahaDBT (Maharashtra Direct Benefit Transfer) is an online portal by the Government of Maharashtra "
                        "for disbursement of scholarships and other benefits directly to eligible beneficiaries. "
                        "Students can apply for various post-matric and pre-matric scholarships through this portal. "
                        "The portal URL is https://mahadbt.maharashtra.gov.in/",
                "title": "About MahaDBT Portal",
                "source": "MahaDBT Official Portal",
                "source_url": "https://mahadbt.maharashtra.gov.in/",
                "scheme_id": "general",
                "category": "overview",
            },
            # ── Post-Matric Scholarship Requirements ──
            {
                "text": "Required documents for MahaDBT Post-Matric Scholarship application typically include: "
                        "1. Caste Certificate (Jaat Pramanpatra) issued by competent authority "
                        "2. Income Certificate (Utpanna Dakhla) showing family annual income "
                        "3. Domicile Certificate (Abhivas Pramanpatra) proving residence in Maharashtra "
                        "4. College Bonafide / Admission Letter from the institution "
                        "5. Previous year marksheet or grade card "
                        "6. Bank passbook first page or cancelled cheque with account details "
                        "7. Aadhaar card for identity verification "
                        "Note: Specific schemes may have additional document requirements.",
                "title": "Required Documents for Post-Matric Scholarship",
                "source": "MahaDBT Application Guide",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/flow",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
            {
                "text": "Income eligibility criteria for post-matric scholarships vary by category: "
                        "For SC/ST category students, the annual family income limit is typically Rs. 2,50,000 (2.5 Lakhs). "
                        "For OBC/VJNT/SBC category students, different income limits may apply depending on the specific scheme. "
                        "The income certificate must be issued by a competent authority (Tahsildar or higher). "
                        "Income certificates are generally valid for one financial year.",
                "title": "Income Eligibility Criteria",
                "source": "MahaDBT Scheme Guidelines",
                "source_url": "https://mahadbt.maharashtra.gov.in/",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
            {
                "text": "The applicant's name must be consistent across all submitted documents. "
                        "Any discrepancy in name spelling between certificates (caste certificate, income certificate, "
                        "marksheet, college bonafide, bank document) may lead to application rejection or delay. "
                        "If there is a name change, a gazette notification or affidavit may be required. "
                        "Common issues include: different spellings of the same name, missing middle name, "
                        "father's name vs surname variations.",
                "title": "Name Consistency Requirement",
                "source": "MahaDBT Application FAQ",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/faq",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
            {
                "text": "Bank account requirements for MahaDBT scholarship: "
                        "1. The bank account must be in the name of the student (applicant) "
                        "2. The account should be active and operational "
                        "3. The account must be linked with Aadhaar for DBT (Direct Benefit Transfer) "
                        "4. Joint accounts may not be accepted for scholarship disbursement "
                        "5. Provide bank passbook first page or cancelled cheque showing account number, IFSC code, "
                        "and account holder name clearly "
                        "6. The name on the bank account must match the applicant's name on other documents",
                "title": "Bank Account Requirements",
                "source": "MahaDBT Application Guide",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/flow",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
            {
                "text": "Domicile certificate (Abhivas Pramanpatra) must certify that the applicant is a domicile "
                        "of Maharashtra. This is mandatory for Maharashtra state scholarships. "
                        "The certificate must be issued by the Tahsildar or competent authority. "
                        "The applicant must have been residing in Maharashtra for the specified period.",
                "title": "Domicile Certificate Requirement",
                "source": "MahaDBT Scheme Guidelines",
                "source_url": "https://mahadbt.maharashtra.gov.in/",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
            {
                "text": "Academic year for the application must match the current admission year. "
                        "The college bonafide certificate must reflect the same academic year as the application. "
                        "Previous year marksheet should be for the immediately preceding academic session. "
                        "Applying for the wrong academic year is a common reason for application issues.",
                "title": "Academic Year Requirements",
                "source": "MahaDBT Application FAQ",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/faq",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
            # ── Application Process ──
            {
                "text": "MahaDBT Application Process: "
                        "Step 1: Register on the MahaDBT portal with valid mobile number and Aadhaar "
                        "Step 2: Complete the profile with personal, academic, and bank details "
                        "Step 3: Select the applicable scholarship scheme "
                        "Step 4: Fill the application form with accurate details "
                        "Step 5: Upload required documents in the specified format and size "
                        "Step 6: Review all details carefully before final submission "
                        "Step 7: Submit the application and note the application number "
                        "Step 8: Track application status through the portal "
                        "Important: Ensure all uploaded documents are clear, legible, and in the accepted format.",
                "title": "Application Process Steps",
                "source": "MahaDBT Application Flow",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/flow",
                "scheme_id": "mahadbt_postmatric",
                "category": "process",
            },
            # ── Common Issues ──
            {
                "text": "Common reasons for MahaDBT application rejection or return: "
                        "1. Name mismatch across documents "
                        "2. Income certificate amount exceeding the scheme limit "
                        "3. Missing or unreadable documents "
                        "4. Wrong academic year on documents "
                        "5. Bank account not in the student's name "
                        "6. Expired certificates "
                        "7. Documents uploaded in wrong format or below minimum quality "
                        "8. Incomplete form filling "
                        "9. Category mismatch between caste certificate and selected category "
                        "10. College not approved or affiliated with the specified university",
                "title": "Common Rejection Reasons",
                "source": "MahaDBT FAQ",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/faq",
                "scheme_id": "mahadbt_postmatric",
                "category": "troubleshooting",
            },
            {
                "text": "If your MahaDBT application is returned with deficiencies: "
                        "1. Log in to the portal and check the specific reason for return "
                        "2. Correct the identified issues in your documents "
                        "3. Re-upload the corrected documents "
                        "4. Resubmit the application before the deadline "
                        "5. Contact the college nodal officer for assistance if needed "
                        "For name correction, an affidavit or gazette notification may be required. "
                        "For income certificate issues, obtain a fresh certificate from the Tahsildar office.",
                "title": "Handling Application Returns",
                "source": "MahaDBT FAQ",
                "source_url": "https://mahadbt.maharashtra.gov.in/home/faq",
                "scheme_id": "mahadbt_postmatric",
                "category": "troubleshooting",
            },
            # ── Category-specific info ──
            {
                "text": "Caste validity certificate may be required in addition to the caste certificate "
                        "for certain categories. The caste certificate must be issued by the competent authority "
                        "(Tahsildar, Sub-Divisional Officer, or Collector). "
                        "For SC/ST categories, the certificate must be in the format prescribed by the "
                        "Government of India. OBC/VJNT/SBC certificates may require additional validation.",
                "title": "Caste Certificate Details",
                "source": "MahaDBT Scheme Guidelines",
                "source_url": "https://mahadbt.maharashtra.gov.in/",
                "scheme_id": "mahadbt_postmatric",
                "category": "requirement",
            },
        ]
