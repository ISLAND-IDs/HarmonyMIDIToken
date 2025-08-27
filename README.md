# HarmonyMIDIToken

> The brand-new MIDI tokenizer based on music21 — designed around Future Bounce workflows and harmonic structure.
> 

![PyPI](https://img.shields.io/pypi/v/harmony-midi-token.svg)

![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

**HarmonyMIDIToken**은 MIDI 토크나이저로, **pitch에 따른 악기(Instrument) 구분이 완료된 Future Bounce MIDI**를 음향학적으로 표현 가능한 JSON과 LSTM을 위한 타임스텝 시퀀스로 직렬화/역직렬화하는 것을 목표로 합니다.
패키지는 PyPI에 `harmony-midi-token` 이름으로 공개되어 있으며, Python 3.11 이상을 요구합니다. ([PyPI](https://pypi.org/project/harmony-midi-token/))

---

## ✨ Key Features

- **music21 기반 파이프라인**: MIDI → 토큰 / 토큰 → MIDI 왕복을 클래식한 음악 정보 구조 위에서 수행
- **모델 친화적 형식**: 생성 모델 학습에 바로 투입 가능한 정수 시퀀스/사전 포맷 제공
- **양방향 변환 보장**: 토큰에서 MIDI로 되돌릴 수 있도록 가역성(reversibility)을 중시한 규칙 설계

---

## 📦 Installation

```bash
pip install harmony-midi-token
# Requires Python 3.11+

```

> 참고: 프로젝트의 라이선스는 MIT이며, 리포지토리는 GitHub에서 공개되어 있습니다.
> 

---

## 🚀 Quick Start

- 아래 예시 코드를 참고하여 사용해 주세요.

```python
from HarmonyMIDIToken import HarmonyMIDIToken

MIDI = HarmonyMIDIToken()
MIDI.set_midi("examples/future_bounce.mid")

MIDI.to_midi() # Music21 Score 객체를 리턴
MIDI.to_json() # JSON 형식의 문자열 리턴

MIDI.token_id # 정수 시퀀스 토큰
MIDI.set_id([128, 100, 10, 79, 2]) # 토큰을 객체로 변환
```

---

## 🤝 Contributing

이슈/PR 환영합니다!

버그 리포트 시 **OS, Python 버전(3.11+), 패키지 버전(예: 0.4.0), 최소 재현 코드**를 포함해 주세요.

PR 작성 시 **어떤 부분을 수정**하였는지, **수정 목적**(예: 몇번 이슈의 버그 수정)를 포함해 주세요

ISLAND 멤버라면, PR 할 필요없이 커밋해도 상관 없으나, 버그나 추가해야 할 사항이 있다면 꼭 이슈를 작성해주세요

---

## 🙏 Acknowledgements

- **music21**
- pychord
