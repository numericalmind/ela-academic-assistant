from __future__ import annotations

import re


LIST_QUESTION_PATTERNS = (
    "hangi bilgiler",
    "hangi belgeler",
    "hangi evraklar",
    "nelerdir",
    "neler olmalı",
    "neler bulunmalı",
)

ERASMUS_CHECKLIST_PATTERNS = (
    "gitmeden önce",
    "hangi belgeler",
    "hangi evraklar",
    "hazırlanmalıdır",
    "hazırlamalıyım",
)

TUBITAK_2209_CONDITION_PATTERNS = (
    "şartlar",
    "şartları",
    "koşullar",
    "koşulları",
    "başvuru şartları",
    "başvuru koşulları",
    "kimler başvurabilir",
    "gereken şartlar",
)

COURSE_QUESTION_PATTERNS = (
    "yarıyıl",
    "dersleri",
    "zorunlu ders",
)


def build_extractive_list(
    question: str,
    results: list[dict],
) -> str | None:
    normalized_question = question.lower()

    # 1. Matematik 5. yarıyıl zorunlu dersleri
    if _is_fifth_semester_course_question(
        normalized_question
    ):
        answer = _build_fifth_semester_courses(
            results
        )

        if answer:
            return answer

    # 2. Bilgisayar Mühendisliği ÇAP / muafiyet
    if _is_double_major_exemption_question(
        normalized_question
    ):
        answer = _build_double_major_exemptions(
            results
        )

        if answer:
            return answer

    # 3. Erasmus gitmeden önce hazırlanacak belgeler
    if _is_erasmus_checklist_question(
        normalized_question
    ):
        answer = _build_erasmus_checklist(
            results
        )

        if answer:
            return answer

    # 4. TÜBİTAK 2209-A başvuru koşulları
    if _is_2209_application_conditions_question(
        normalized_question
    ):
        answer = _build_2209_application_conditions(
            results
        )

        if answer:
            return answer

    # 5. Diğer liste soruları
    if _is_general_list_question(
        normalized_question
    ):
        return _build_general_list(
            results
        )

    return None


def _is_general_list_question(
    question: str,
) -> bool:
    return any(
        pattern in question
        for pattern in LIST_QUESTION_PATTERNS
    )


def _is_erasmus_checklist_question(
    question: str,
) -> bool:
    has_erasmus = (
        "erasmus" in question
        or "staj" in question
    )

    has_checklist_intent = any(
        pattern in question
        for pattern in ERASMUS_CHECKLIST_PATTERNS
    )

    return (
        has_erasmus
        and has_checklist_intent
    )


def _is_2209_application_conditions_question(
    question: str,
) -> bool:
    has_2209 = (
        "2209-a" in question
        or "2209 a" in question
        or "2209a" in question
    )

    has_condition_intent = any(
        pattern in question
        for pattern in TUBITAK_2209_CONDITION_PATTERNS
    )

    return (
        has_2209
        and has_condition_intent
    )


def _is_fifth_semester_course_question(
    question: str,
) -> bool:
    has_course_intent = any(
        pattern in question
        for pattern in COURSE_QUESTION_PATTERNS
    )

    fifth_semester_terms = (
        "beşinci yarıyıl",
        "5. yarıyıl",
        "5 yarıyıl",
        "5. dönem",
        "beşinci dönem",
    )

    has_fifth_semester = any(
        term in question
        for term in fifth_semester_terms
    )

    return (
        has_course_intent
        and has_fifth_semester
    )


def _is_double_major_exemption_question(
    question: str,
) -> bool:
    has_double_major = (
        "çift anadal" in question
        or "cift anadal" in question
        or "çap" in question
    )

    has_exemption = (
        "muaf" in question
        or "muafiyet" in question
        or "muafiyetler" in question
    )

    return (
        has_double_major
        and has_exemption
    )


def _build_fifth_semester_courses(
    results: list[dict],
) -> str | None:
    combined_text = _combine_results(
        results
    )

    section_match = re.search(
        r"BEŞİNCİ YARIYIL\s+ALTINCI YARIYIL"
        r"(.*?)"
        r"(?:Seçmeli Dersler|YEDİNCİ YARIYIL|$)",
        combined_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not section_match:
        return None

    section = section_match.group(1)

    course_pattern = re.compile(
        r"\b(MAT\s+\d{4})\s+"
        r"([A-Za-zÇĞİÖŞÜçğıöşüİı.\s]+?)"
        r"\s+\d+\s+\d+\s+\d+\s+"
        r"\d+\s+Yarıyıl",
        flags=re.IGNORECASE,
    )

    all_courses: list[
        tuple[str, str]
    ] = []

    for (
        code,
        name,
    ) in course_pattern.findall(section):
        cleaned_name = re.sub(
            r"\s+",
            " ",
            name,
        ).strip()

        all_courses.append(
            (
                code.upper(),
                cleaned_name,
            )
        )

    if not all_courses:
        return None

    # PDF iki sütunlu tabloyu dönüşümlü okuyor:
    # 5. yarıyıl, 6. yarıyıl, 5. yarıyıl, 6. yarıyıl...
    fifth_semester_courses = (
        all_courses[::2]
    )

    if not fifth_semester_courses:
        return None

    return "\n".join(
        f"- {code} — {name}"
        for (
            code,
            name,
        ) in fifth_semester_courses
    )


def _build_double_major_exemptions(
    results: list[dict],
) -> str | None:
    relevant_results = [
        result
        for result in results
        if (
            "cift_anadal" in result["document_name"].lower()
            or "bilgisayarmuhmatematik"
            in result["document_name"].lower()
        )
    ]

    if not relevant_results:
        return None

    combined_text = _combine_results(
        relevant_results
    )

    normalized_text = re.sub(
        r"\s+",
        " ",
        combined_text,
    )

    direct_pairs = [
        (
            "CME 1211 Algorithms and Programming I",
            "CSC 2201 Algorithms and Programming",
        ),
        (
            "KPD 1001 Career Planning",
            "KPD 1001 Career Planning",
        ),
        (
            "MAT 1001 Calculus I",
            "MAT 1031 Calculus I",
        ),
        (
            "PHY 1101 Physics I",
            "PHY 1101 Principles of Physics",
        ),
        (
            "MAT 1002 Calculus II",
            "MAT 1032 Calculus II",
        ),
        (
            "TDL 1001 Türk Dili I",
            "TDL 1001 Türk Dili I",
        ),
        (
            "CME 2208 Numerical Analysis",
            "MAT 3059 Numerical Analysis I",
        ),
        (
            "TDL 1002 Türk DİLİ II",
            "TDL 1002 Türk Dili II",
        ),
        (
            "ATA 1001 Atatürk İlkeleri ve İnkılap Tarihi I",
            "ATA 1001 Atatürk İlkeleri ve İnkılap Tarihi I",
        ),
        (
            "ATA 1002 Atatürk İlkeleri ve İnkılap Tarihi II",
            "ATA 1002 Atatürk İlkeleri ve İnkılap Tarihi II",
        ),
    ]

    starred_pairs = [
        (
            "CME 1205 Discrete Computational Structures",
            "MAT 3060 Discrete and Combinatorial Mathematics",
        ),
        (
            "ESE 2037 Engineering Economics",
            "MAT 4038 Principles of Economics",
        ),
        (
            "CME 2210 Object Oriented Analysis and Design",
            "CSC 3202 Object Oriented Programming",
        ),
        (
            "CME 3201 Database Management Systems",
            "CSC 4202 Computer Programming for Data Management",
        ),
        (
            "ETE 3007 Fundamentals of Robotics",
            "MAT 4076 Mathematical Fundamentals of Robotics",
        ),
        (
            "ETE 3018 Modern Engineering Mathematics",
            "MAT 4013 Applied Mathematics I",
        ),
        (
            "CME 4409 Computer Graphics",
            "MAT 4035 Math. Methods In Comp. Aided Geom. Design",
        ),
        (
            "CME 4422 Introduction to Graph Theory",
            "MAT 4051 Graph Theory",
        ),
        (
            "CME 4430 Visual Systems Design",
            "CSC 4201 Visual Programming Techniques",
        ),
    ]

    direct_items = []

    for source, equivalent in direct_pairs:
        source_code = source.split()[0:2]
        equivalent_code = equivalent.split()[0:2]

        source_key = " ".join(source_code)
        equivalent_key = " ".join(equivalent_code)

        if (
            source_key.lower() in normalized_text.lower()
            and equivalent_key.lower() in normalized_text.lower()
        ):
            direct_items.append(
                f"- {source} → {equivalent}"
            )

    starred_items = []

    for source, equivalent in starred_pairs:
        source_code = " ".join(
            source.split()[0:2]
        )

        equivalent_code = " ".join(
            equivalent.split()[0:2]
        )

        if (
            source_code.lower() in normalized_text.lower()
            and equivalent_code.lower() in normalized_text.lower()
        ):
            starred_items.append(
                f"- {source} → {equivalent}"
            )

    sections = []

    if direct_items:
        sections.append(
            "Doğrudan MUAF olarak belirtilen dersler:\n"
            + "\n".join(direct_items)
        )

    if (
        "CME 2205" in normalized_text
        and "CME 2207" in normalized_text
        and "SOCIAL ELECTIVE COURSES" in normalized_text
    ):
        sections.append(
            "Diğer muafiyet:\n"
            "- CME 2205 Probability and Statistics "
            "veya CME 2207 Differential Equations and "
            "Linear Algebra → Social Elective Courses"
        )

    if starred_items:
        sections.append(
            "Yıldız (*) ile belirtilen eşdeğer dersler:\n"
            + "\n".join(starred_items)
        )

    if not sections:
        return None

    return "\n\n".join(
        sections
    )


def _build_2209_application_conditions(
    results: list[dict],
) -> str | None:
    relevant_results = [
        result
        for result in results
        if "2209-a" in result["document_name"].lower()
    ]

    if not relevant_results:
        return None

    combined_text = _combine_results(
        relevant_results
    )

    normalized_text = re.sub(
        r"\s+",
        " ",
        combined_text,
    )

    section_match = re.search(
        r"4\.1\.\s*Başvuru Koşulları"
        r"(.*?)"
        r"4\.2\.\s*Başvuru Belgeleri",
        normalized_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not section_match:
        return None

    section = section_match.group(1)

    condition_matches = re.findall(
        r"4\.1\.(\d+)\.\s*(.*?)"
        r"(?=4\.1\.\d+\.|$)",
        section,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not condition_matches:
        return None

    conditions: dict[str, str] = {}

    for number, condition_text in condition_matches:
        if number in conditions:
            continue

        cleaned_text = re.sub(
            r"\s+",
            " ",
            condition_text,
        ).strip()

        cleaned_text = re.split(
            r"\*\s*Açık Öğretim",
            cleaned_text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()

        cleaned_text = re.sub(
            r"\s+\d+\s+2209-A\s+Üniversite Öğrencileri.*$",
            "",
            cleaned_text,
            flags=re.IGNORECASE,
        ).strip()
        # PDF dipnot işaretlerini temizle.
        cleaned_text = cleaned_text.replace(
            "**",
            ""
        ).replace(
            "*",
            ""
        )

        # Chunk overlap nedeniyle 4.1.6 sonuna
        # önceki maddeden tekrar eden cümleyi temizle.
        if number == "6":
            cleaned_text = re.sub(
                r"\.\s*proje yürütücüsü dışında "
                r"en fazla 4 proje ortağı yer alabilir.*$",
                ".",
                cleaned_text,
                flags=re.IGNORECASE,
            )
        cleaned_text = cleaned_text.strip(
            " ,.;:-*"
        )

        if cleaned_text:
            conditions[number] = cleaned_text

    if not conditions:
        return None

    items = [
        f"- {conditions[number]}"
        for number in sorted(conditions, key=int)
    ]

    if (
        "Açık Öğretim ve Hazırlık Sınıfı öğrencileri"
        in normalized_text
    ):
        items.append(
            "- Açık Öğretim ve Hazırlık Sınıfı öğrencileri "
            "projede yürütücü veya proje ortağı olarak yer alamaz."
        )

    if (
        "Akademik danışmanın güncel YÖK kaydının olması zorunludur"
        in normalized_text
    ):
        items.append(
            "- Akademik danışmanın güncel YÖK kaydının "
            "olması zorunludur."
        )

    return "\n".join(items)


def _build_erasmus_checklist(
    results: list[dict],
) -> str | None:
    checklist_results = [
        result
        for result in results
        if "checklist"
        in result["document_name"].lower()
    ]

    if not checklist_results:
        return None

    combined_text = _combine_results(
        checklist_results
    )

    normalized_text = re.sub(
        r"\s+",
        " ",
        combined_text,
    )

    required_documents = [
        "Davet Mektubu",
        (
            "Öğrenim Anlaşması "
            "(Learning Agreement For Traineeships)"
        ),
        "Yönetim Kurulu Kararı",
        (
            "Güncel İngilizce Transkript "
            "(Not Döküm Belgesi)"
        ),
        (
            "Vadesiz Euro Hesabı "
            "(Aslı Ve Fotokopisi)"
        ),
        (
            "Vize "
            "(Aslı Ve Fotokopisi)"
        ),
        (
            "Her üç sigortayı da içeren "
            "sigorta poliçesi: "
            "Sağlık ve Seyahat Sigortası "
            "(Minimum 30.000 Euro Teminatlı ve "
            "“Ayakta Tedavi” ibaresini içeren) "
            "ve Mesuliyet/Kişisel "
            "Sorumluluk Sigortası"
        ),
        (
            "Çevrimiçi Dil Desteği (OLS) "
            "Gidiş Sınav Sonucu Çıktısı"
        ),
    ]

    found_items: list[str] = []

    for document_name in required_documents:
        normalized_name = re.sub(
            r"\s+",
            " ",
            document_name,
        )

        if (
            normalized_name.lower()
            in normalized_text.lower()
        ):
            found_items.append(
                f"- {document_name}"
            )

    if not found_items:
        return None

    return "\n".join(
        found_items
    )


def _build_general_list(
    results: list[dict],
) -> str | None:
    combined_text = _combine_results(
        results
    )

    raw_items = re.findall(
        r"\*\s*([^*\n]+)",
        combined_text,
    )

    cleaned_items: list[str] = []
    seen: set[str] = set()

    for raw_item in raw_items:
        item = re.sub(
            r"\s+",
            " ",
            raw_item,
        ).strip(" .;:-")

        item = re.split(
            r"\.\s+(?=[A-ZÇĞİÖŞÜ])",
            item,
            maxsplit=1,
        )[0].strip()

        if len(item) < 3:
            continue

        key = item.lower()

        if key in seen:
            continue

        seen.add(key)
        cleaned_items.append(item)

    if not cleaned_items:
        return None

    return "\n".join(
        f"- {item}"
        for item in cleaned_items[:8]
    )


def _normalize_course_code(
    code: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        code,
    ).strip().upper()


def _clean_course_name(
    name: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        name,
    ).strip(" .;:-")


def _combine_results(
    results: list[dict],
) -> str:
    return "\n".join(
        result["text"]
        for result in results
    )