import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from openai import OpenAI
from config import settings


@dataclass
class HearingSummary:
    hearing_title: str
    summary: str
    key_points: List[str]
    complainants_concerns: List[str]
    officials_responses: List[str]
    noise_level_analysis: Dict[str, Any]
    zoning_recommendations: List[Dict[str, Any]]
    priority_level: str
    estimated_impact: str


class SummaryGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_hearing_summary(
        self,
        hearing_data: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]],
        noise_data: Dict[str, Any]
    ) -> HearingSummary:
        """
        Generate a comprehensive summary of a noise hearing using OpenAI.
        """
        complainant_text = []
        official_text = []

        for seg in transcript_segments:
            role = seg.get('speaker_role')
            text = seg.get('text', '')
            if role == 'complainant':
                complainant_text.append(text)
            elif role == 'official':
                official_text.append(text)

        full_transcript = '\n'.join([
            f"[{seg.get('speaker_role', 'unknown')}]: {seg.get('text', '')}"
            for seg in transcript_segments
        ])

        system_prompt = """你是一名智慧城市噪声管理专家。请分析噪声听证会的转录内容，
        生成专业的摘要和区划调整建议。请用中文回复，保持客观、专业的语气。"""

        user_prompt = f"""
        听证会标题: {hearing_data.get('title', '未命名听证会')}
        时间: {hearing_data.get('scheduled_at', '未知')}
        地点/区域: {hearing_data.get('district', '未知区域')}
        描述: {hearing_data.get('description', '无描述')}

        噪声监测数据:
        {json.dumps(noise_data, ensure_ascii=False, indent=2)}

        完整转录内容:
        {full_transcript[:8000]}

        请分析以上内容，生成以下JSON格式的结果:
        {{
            "summary": "听证会的整体摘要（200-300字）",
            "key_points": ["要点1", "要点2", "要点3", ...],
            "complainants_concerns": ["投诉者的主要诉求1", "诉求2", ...],
            "officials_responses": ["官员的回应要点1", "回应要点2", ...],
            "noise_level_analysis": {{
                "average_level": 平均分贝值,
                "max_level": 最大分贝值,
                "exceeds_standard": 是否超标（布尔值）,
                "standard_violation": "违反的标准描述",
                "affected_areas": ["受影响区域1", "区域2"]
            }},
            "zoning_recommendations": [
                {{
                    "type": "调整类型（如：缓冲区、噪声隔离带、限制区域等）",
                    "area": "涉及区域",
                    "description": "具体建议描述",
                    "priority": "优先级（high/medium/low）",
                    "estimated_effect": "预期效果"
                }}
            ],
            "priority_level": "整体优先级（critical/high/medium/low）",
            "estimated_impact": "预计影响范围和人群描述"
        }}
        """

        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=3000
        )

        result = json.loads(response.choices[0].message.content)

        return HearingSummary(
            hearing_title=hearing_data.get('title', '未命名听证会'),
            summary=result.get('summary', ''),
            key_points=result.get('key_points', []),
            complainants_concerns=result.get('complainants_concerns', []),
            officials_responses=result.get('officials_responses', []),
            noise_level_analysis=result.get('noise_level_analysis', {}),
            zoning_recommendations=result.get('zoning_recommendations', []),
            priority_level=result.get('priority_level', 'medium'),
            estimated_impact=result.get('estimated_impact', '')
        )

    def generate_markdown_report(
        self,
        summary: HearingSummary,
        hearing_data: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a Markdown report from the summary.
        """
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

        priority_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }.get(summary.priority_level, '⚪')

        md = f"""# 噪声听证会纪要报告

**生成时间**: {now}
**听证会标题**: {summary.hearing_title}
**优先级**: {priority_emoji} {summary.priority_level}
**预计影响**: {summary.estimated_impact}

---

## 一、听证会概述

{summary.summary}

### 基本信息
- **时间**: {hearing_data.get('scheduled_at', '未知')}
- **区域**: {hearing_data.get('district', '未知')}
- **描述**: {hearing_data.get('description', '无')}

---

## 二、关键要点

{self._list_to_markdown(summary.key_points)}

---

## 三、投诉者诉求

{self._list_to_markdown(summary.complainants_concerns)}

---

## 四、官方回应

{self._list_to_markdown(summary.officials_responses)}

---

## 五、噪声水平分析

| 指标 | 数值 |
|------|------|
| 平均噪声水平 | {summary.noise_level_analysis.get('average_level', 'N/A')} dB |
| 最大噪声水平 | {summary.noise_level_analysis.get('max_level', 'N/A')} dB |
| 是否超标 | {'是' if summary.noise_level_analysis.get('exceeds_standard') else '否'} |
| 违反标准 | {summary.noise_level_analysis.get('standard_violation', '无')} |

### 受影响区域
{self._list_to_markdown(summary.noise_level_analysis.get('affected_areas', []))}

---

## 六、区划调整建议

"""

        for i, rec in enumerate(summary.zoning_recommendations, 1):
            rec_priority = rec.get('priority', 'medium')
            rec_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(rec_priority, '⚪')

            md += f"""### 建议 {i}: {rec.get('type', '未分类')} {rec_emoji}

- **涉及区域**: {rec.get('area', '未知')}
- **优先级**: {rec_priority}
- **具体建议**: {rec.get('description', '')}
- **预期效果**: {rec.get('estimated_effect', '')}

"""

        md += """---

## 七、完整对话记录

"""

        current_role = None
        for seg in transcript_segments:
            role = seg.get('speaker_role', 'unknown')
            role_cn = {
                'complainant': '👤 投诉者',
                'official': '👔 官员',
                'unknown': '❓ 未知'
            }.get(role, '❓ 未知')

            if role != current_role:
                md += f"\n**{role_cn}**:\n"
                current_role = role

            time_str = f"[{self._format_time(seg.get('start_time', 0))}]"
            md += f"{time_str} {seg.get('text', '')}\n"

        md += f"\n\n---\n*本报告由智慧城市噪声听证会系统自动生成*"

        return md

    def _list_to_markdown(self, items: List[str]) -> str:
        if not items:
            return "无"
        return '\n'.join([f"- {item}" for item in items])

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
