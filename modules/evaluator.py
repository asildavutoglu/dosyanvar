"""Gemini API'sini kullanarak CV'yi verilen kriterlere göre değerlendirir.

hiring-agent'ın "adayı işverene göre puanlama" mantığını tersine çevirip
"kendi CV'ni ilana göre değerlendir" akışına uyarladık.
"""

import json
import os
import re

import requests

GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

SYSTEM_PROMPT = """\
Sen deneyimli, adil ve doğrudan konuşan bir işe alım danışmanısın. Görevin, bir
adayın kendi CV'sini verilen iş kriterlerine/ilanına göre değerlendirmesine
yardımcı olmak. Bir işverenin bakış açısıyla objektif değerlendir ama adaya
gelişimi için somut, uygulanabilir tavsiyeler ver.

Kesinlikle sadece geçerli JSON döndür, başka hiçbir metin ekleme (markdown
kod bloğu, açıklama, selamlama vb. YOK). JSON şu şemaya uymalı:

{
  "overall_score": <0-100 arası tam sayı>,
  "overall_summary": "<2-3 cümlelik özet, ikinci tekil şahısla 'sen' diye hitap et>",
  "criteria_breakdown": [
    {
      "criterion": "<kriterin kısa adı>",
      "score": <0-100 arası tam sayı>,
      "status": "<'güçlü' | 'kısmi' | 'eksik' içinden biri>",
      "evidence": "<CV'den bulunan somut kanıt, yoksa 'CV'de buna dair kanıt bulunamadı' yaz>",
      "gap": "<eksik veya zayıf olan kısım, güçlüyse boş string olabilir>",
      "suggestion": "<CV'yi veya profili nasıl güçlendirebileceğine dair somut, uygulanabilir bir öneri>"
    }
  ],
  "top_improvements": ["<en etkili 3-5 iyileştirme, önem sırasına göre>"],
  "strengths": ["<CV'nin öne çıkan 2-4 güçlü yönü>"]
}

Kriterleri, verilen iş ilanı/kriter metninden kendin çıkar (madde madde
değilse bile anlamlı parçalara böl). En az 3, en fazla 8 kriter üret.
Eğer GitHub verisi verilmişse, açık kaynak katkısı veya kişisel proje
gerektiren kriterlerde bu veriyi kanıt olarak kullan.
"""


def _build_user_prompt(resume_text: str, criteria: str, github_data: dict | None) -> str:
    parts = [
        "### DEĞERLENDİRİLECEK KRİTERLER / İŞ İLANI ###",
        criteria.strip(),
        "",
        "### CV METNİ ###",
        resume_text.strip(),
    ]
    if github_data:
        parts.extend(
            [
                "",
                "### GITHUB SİNYALLERİ ###",
                json.dumps(github_data, ensure_ascii=False, indent=2),
            ]
        )
    return "\n".join(parts)


def _extract_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return json.loads(cleaned)


def evaluate_resume(resume_text: str, criteria: str, github_data: dict | None = None) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY tanımlı değil. .env dosyana Gemini API anahtarını ekle."
        )

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = GEMINI_API_URL_TEMPLATE.format(model=model)

    user_prompt = _build_user_prompt(resume_text, criteria, github_data)

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "response_mime_type": "application/json",
        },
    }

    response = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Gemini API hatası ({response.status_code}): {response.text[:500]}")

    data = response.json()
    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini yanıtı beklenmedik formatta: {data}") from exc

    try:
        result = _extract_json(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini yanıtı geçerli JSON değil: {exc}") from exc

    return result
