#!/usr/bin/env python3
"""Generate two end-to-end dogfood projects for short-drama-scriptwriter.

This is a validation harness, not part of the normal writing workflow. It creates
one 60-episode domestic AI comic drama and one 60-episode TikTok/US project with
formal planning files, episode drafts, simulated process notes, and enhanced
delivery seed files for the overseas project.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECTS_DIR = ROOT / "projects"
GENERATED_AT = datetime.now().strftime("%Y-%m-%d %H:%M")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def project_state(delivery_mode: str = "standard") -> str:
    state = {
        "currentStep": "交付整合",
        "projectPhase": "交付",
        "lastCompletedPhase": "全剧复核已通过",
        "deliveryMode": delivery_mode,
        "outlineProgress": {
            "completedRanges": ["001-060"],
            "currentRange": "",
            "nextRange": "",
            "allOutlineGenerated": True,
        },
        "scriptProgress": {
            "completedRanges": ["001-010", "011-020", "021-030", "031-040", "041-050", "051-060"],
            "currentRange": "",
            "nextRange": "",
            "fullScriptReviewDone": True,
        },
        "changeControl": {
            "pendingRollback": False,
            "sourceStep": "",
            "sourceFiles": [],
            "affectedGates": [],
            "reason": "",
            "triggeredAt": "",
            "resolvedAt": GENERATED_AT,
        },
        "lastQcStep": "交付质检",
        "lastIndependentReviewMode": "dogfood-simulated",
        "lastStateUpdatedAt": GENERATED_AT,
        "qcStatus": {
            "kickoff": "已通过",
            "planningFoundation": "已通过",
            "planningStructure": "已通过",
            "outline": "已通过",
            "scriptBatches": [
                {"range": "001-010", "status": "已通过"},
                {"range": "011-020", "status": "已通过"},
                {"range": "021-030", "status": "已通过"},
                {"range": "031-040", "status": "已通过"},
                {"range": "041-050", "status": "已通过"},
                {"range": "051-060", "status": "已通过"},
            ],
            "delivery": "未检查",
        },
        "dogfoodNote": "本项目用于端到端测试；质检记录模拟真实编剧回退，不代表 production clean-context 放行。",
    }
    return json.dumps(state, ensure_ascii=False, indent=2)


CN_PHASES = [
    ("开篇卷入", "被迫签字", "父亲事故旧案", "荣曜集团公关压迫", "旧补充协议"),
    ("入局取证", "进入调解中心", "拆迁流水异常", "律师函与切流", "业主联名册"),
    ("身份翻面", "夺回证据链", "母亲失踪线索", "伪证人与内鬼", "旧公证录音"),
    ("公开清算", "推动听证", "城改验收造假", "行政投诉反噬", "验收照片原件"),
    ("低谷重组", "保护证人", "父亲真正死因", "关系背刺", "急救转运单"),
    ("终局开庭", "申请再审", "资本保护伞", "终审前夜威胁", "原始账册"),
]


US_PHASES = [
    ("Hook and Threat", "refuse the NDA", "a forged trust clause", "a campus rumor push", "the unsigned rider"),
    ("Inside the Machine", "enter Hale House", "the shadow-ban dashboard", "a restraining order threat", "the moderator logs"),
    ("Identity Turn", "prove the inheritance trail", "Ava's birth record", "a planted witness", "the sealed voicemail"),
    ("Public Pressure", "force a board hearing", "the scholarship laundering route", "a cancellation campaign", "the donor list"),
    ("Lowest Point", "protect the whistleblower", "the hospital cover-up", "Mason's betrayal", "the ambulance record"),
    ("Final Hearing", "break the trust vote", "the original ledger", "Veronica's last NDA", "the board minutes"),
]


def episode_plan(number: int, phases: list[tuple[str, str, str, str, str]]) -> dict[str, str]:
    phase_index = min((number - 1) // 10, len(phases) - 1)
    phase, action, secret, pressure, asset = phases[phase_index]
    turn = ["反签", "截证", "换场", "逼供", "公开视频", "申请复核", "借对手手", "护证人", "反向设局", "留尾钩"][(number - 1) % 10]
    hook = [
        "关键证人突然改口",
        "旧文件多出一页",
        "对手先一步报警",
        "同盟递来反证",
        "直播间被切断",
        "主角收到匿名坐标",
        "家人被推到台前",
        "证据被当场调包",
        "上级要求停手",
        "最终名单露出一个熟人",
    ][(number - 1) % 10]
    return {
        "phase": phase,
        "action": action,
        "secret": secret,
        "pressure": pressure,
        "asset": asset,
        "turn": turn,
        "hook": hook,
    }


def cn_outline_entries() -> tuple[str, str]:
    rows = []
    details = []
    for i in range(1, 61):
        ep = episode_plan(i, CN_PHASES)
        rows.append(
            f"| EP{i:03d} | 江闻雪{ep['action']}，用{ep['asset']}逼近{ep['secret']} | "
            f"她把{ep['pressure']}变成反击入口 | {ep['turn']} | 证据/尊严 | "
            f"{ep['secret']}被看见一角 | {ep['hook']} |"
        )
        details.append(
            f"### EP{i:03d}\n\n"
            f"- 本集定位：{ep['phase']}第{(i - 1) % 10 + 1}步，推进{ep['secret']}。[MUST]\n"
            f"- 本集观众一句话（低术语版本）：江闻雪被{ep['pressure']}逼到墙角，反用{ep['asset']}撬开局面。[MUST]\n"
            f"- 开场承接：{'无可承接' if i == 1 else f'承接 EP{i-1:03d} 的尾钩。'} [MUST]\n"
            f"- 本集主要出场角色：江闻雪 / 梁策 / 周曼丽 / 荣曜相关人。[MUST]\n"
            f"- 本集主要冲突：公开证据前，被对手用制度和舆论同时压回去。[MUST]\n"
            f"- 本集回报类型：证据推进 + 情绪反击。[MUST]\n"
            f"- 本集主要回报：观众看到{ep['secret']}有实质证据。[MUST]\n"
            f"- 本集过程链：被压 -> 找证 -> 被截 -> 换打法 -> 留出{ep['hook']}。[MUST]\n"
            f"- 本集场次承载表：1-1 压迫；1-2 取证；1-3 翻面尾钩。[MUST]\n"
            f"- 本集剧作层追更设计：情绪回报是{ep['secret']}被看见一角；尾钩 {ep['hook']} 改变下一集取证目标。[MUST]\n"
            f"- 结尾钩子：{ep['hook']}。[MUST]\n"
            f"- 下一集接口：从{ep['hook']}继续追证。[MUST]\n"
        )
    return "\n".join(rows), "\n\n".join(details)


def us_outline_entries() -> tuple[str, str]:
    rows = []
    details = []
    for i in range(1, 61):
        ep = episode_plan(i, US_PHASES)
        rows.append(
            f"| EP{i:03d} | Ava {ep['action']} and finds {ep['asset']} | "
            f"她把 {ep['pressure']} 变成公开压力 | {ep['turn']} | Identity/Power | "
            f"{ep['secret']} gets one visible proof | {ep['hook']} |"
        )
        details.append(
            f"### EP{i:03d}\n\n"
            f"- 本集定位：{ep['phase']} step {(i - 1) % 10 + 1}，推进 {ep['secret']}。[MUST]\n"
            f"- 本集观众一句话（低术语版本）：Ava 被 {ep['pressure']} 压住，却用 {ep['asset']} 反逼 Hale 家族。[MUST]\n"
            f"- 开场承接：{'无可承接' if i == 1 else f'承接 EP{i-1:03d} 的尾钩。'} [MUST]\n"
            f"- 本集主要出场角色：Ava Reed / Mason Hale / Veronica Hale / June Park。[MUST]\n"
            f"- 本集主要冲突：Ava 想公开证据，Veronica 用 NDA、名誉和 board pressure 压回去。[MUST]\n"
            f"- 本集回报类型：身份推进 + 权力反击。[MUST]\n"
            f"- 本集主要回报：观众看到 {ep['secret']} 的可验证证据。[MUST]\n"
            f"- 本集过程链：threat -> clue -> public pressure -> counter -> {ep['hook']}。[MUST]\n"
            f"- 本集场次承载表：1-1 threat；1-2 clue；1-3 turn/cliffhanger。[MUST]\n"
            f"- 本集剧作层追更设计：情绪回报是 {ep['secret']} gets one visible proof；尾钩 {ep['hook']} changes next episode's target。[MUST]\n"
            f"- 结尾钩子：{ep['hook']}。[MUST]\n"
            f"- 下一集接口：从 {ep['hook']} 继续推进。[MUST]\n"
        )
    return "\n".join(rows), "\n\n".join(details)


def cn_episode(number: int) -> str:
    ep = episode_plan(number, CN_PHASES)
    title = f"第{number:03d}集"
    return f"""# {title}

## 本集创作简卡

- 开场承接：{'无可承接' if number == 1 else f'承接第{number - 1:03d}集尾钩。'}
- `1-1` 第一动作或第一句对白：江闻雪把签字笔按回桌面。
- 本集戏剧单位：{ep['phase']} / {ep['action']}。
- 本集观众一句话（低术语版本）：江闻雪被{ep['pressure']}压住，反用{ep['asset']}撬出{ep['secret']}。
- 本集情绪落点：被羞辱后的克制反击。
- 本集最小状态变化：对手少一个遮羞口径，江闻雪多一个公开筹码。
- 本集观看回报：{ep['secret']}露出实证。
- 本集可见后果：周曼丽必须临时换人灭火。
- 结尾钩子：{ep['hook']}。

## 场次正文

### {number}-1 日内 城改调解室

- 场景目标：让江闻雪签下不追责协议。
- 场景状态差量：江闻雪从被围攻变成稳住桌面。
- 可见后果：周曼丽第一次露出急躁。

人物：江闻雪 / 梁策 / 周曼丽 / 调解员

△ 调解员把协议推到江闻雪面前，红章压在父亲名字上。
周曼丽：签了，钱今天到账。
江闻雪：这不是赔偿，是封口。
△ 梁策想拦，两个保安往前一步，挡住门口。
周曼丽：你爸欠的账，也该你还。
江闻雪：那就从账开始查。
VO：走廊里有人喊，荣曜的人来了。
△ 江闻雪把签字笔按回桌面，笔尖划破协议第一页。
梁策：你手里有东西？
江闻雪：有一页，他们不敢让我念。
SFX：门锁咔哒一声落下。
△ 周曼丽的笑停住，调解员伸手去抢那页纸。

### {number}-2 日外 老楼外墙

- 场景目标：确认{ep['asset']}是否真实。
- 场景状态差量：线索从传闻变成可拍证据。
- 可见后果：江闻雪被迫暴露行踪。

人物：江闻雪 / 梁策 / 老业主 / 荣曜外勤

△ 老业主掀开铁皮，墙缝里露出被油布包住的旧档案袋。
老业主：你爸当年也来问过。
江闻雪：他问完之后，就出事了。
△ 荣曜外勤举起手机，对准江闻雪的脸。
荣曜外勤：非法闯入，拍清楚。
梁策：这是公共楼道。
△ 江闻雪没有躲，把档案袋放到镜头前。
江闻雪：那你也拍清楚这枚章。
老业主：这是拆前验收章。
梁策：日期对不上。
SFX：楼下传来急刹车声。
△ 江闻雪把档案袋塞进怀里，转身冲向楼梯。

### {number}-3 夜内 梁策律所

- 场景目标：把本集证据变成下一集可用筹码。
- 场景状态差量：证据可用，但新风险出现。
- 可见后果：尾钩指向{ep['hook']}。

人物：江闻雪 / 梁策 / 周曼丽

△ 扫描仪一页页吐出纸，日期、章号、签名排成一条线。
梁策：这能证明验收造假。
江闻雪：不够，还差谁批的。
△ 电脑突然断网，上传进度卡在九成。
周曼丽：别白费劲了。
江闻雪：你怕的不是文件，是我念出来。
△ 梁策拔下硬盘，屋外灯光一盏盏熄灭。
梁策：有人进楼。
江闻雪：把门开着。
周曼丽：你疯了？
SFX：电梯停在本层，叮。
△ 江闻雪站到门口，把硬盘举到摄像头前。

## 本集回填

- 新增悬念：{ep['hook']}。
- 已兑现悬念：{ep['asset']}证明{ep['secret']}有实体线索。
- 关系变化：梁策从旁观协助转向主动保护。
- 资产变化：{ep['asset']}进入证据链。
- 下一集必须承接：江闻雪如何处理{ep['hook']}。

【{title}完】
"""


def us_episode(number: int) -> str:
    ep = episode_plan(number, US_PHASES)
    title = f"EP{number:03d}"
    return f"""# {title}

## 本集创作简卡

- 开场承接：{'无可承接' if number == 1 else f'承接 EP{number - 1:03d} 尾钩。'}
- `1-1` 第一动作或第一句对白：Ava slides the NDA back across the table.
- 本集戏剧单位：{ep['phase']} / {ep['action']}。
- 本集观众一句话（低术语版本）：Ava is cornered by {ep['pressure']}, then uses {ep['asset']} to expose {ep['secret']}。
- 本集情绪落点：public shame turns into controlled defiance。
- 本集最小状态变化：Veronica loses one clean story; Ava gains one public lever。
- 本集观看回报：{ep['secret']} becomes visible proof。
- 本集可见后果：Hale House has to change its cover story。
- 结尾钩子：{ep['hook']}。

## 场次正文

### {number}-1 DAY INT. Trust Office / 日内 信托办公室

- 场景目标：force Ava to sign the NDA.
- 场景状态差量：Ava goes from isolated to visibly dangerous.
- 可见后果：Veronica stops smiling.

人物：Ava Reed（主角） / Mason Hale / Veronica Hale / Board Clerk

△ The clerk places the NDA in front of Ava, covering her father's name.
Veronica Hale: Sign it, and you walk out paid.（她用钱压人。）
Ava Reed: That's not payment. That's a muzzle.（Ava不接封口。）
△ Mason reaches for the pen, but Ava keeps her hand on the folder.
Mason Hale: Ava, don't make this worse.（他想息事宁人。）
Ava Reed: Worse for who?（她反问立场。）
VO：A phone buzzes from inside Veronica's bag.
△ Ava slides the NDA back across the table without looking down.
Veronica Hale: You have no leverage.（反派轻敌。）
Ava Reed: Then why are you sweating?（她戳破心虚。）
SFX：The office door clicks shut.
△ Veronica's smile drops as Ava opens {ep['asset']}.

### {number}-2 DUSK EXT. Campus Steps / 傍晚 校园台阶

- 场景目标：turn {ep['asset']} into public pressure.
- 场景状态差量：the clue moves from private fear to public witness.
- 可见后果：Ava's location is exposed.

人物：Ava Reed / June Park / Mason Hale / Campus Guard

△ June holds her phone low, filming only Ava's hands and the document.
June Park: Keep your face out of it.（朋友保护她。）
Ava Reed: No. They used my face first.（Ava选择公开。）
△ A campus guard steps between Ava and the stairs.
Campus Guard: You're not allowed here.（校警挡路。）
Ava Reed: Show me the order.（她要看依据。）
△ Mason appears behind the guard, jaw tight.
Mason Hale: I can fix this quietly.（他想私了。）
Ava Reed: Quiet is how she wins.（她拒绝沉默。）
June Park: Ava, the stream's lagging.（切流预警。）
△ Ava lifts {ep['asset']} into the frame before the feed drops.
SFX：The livestream audio cuts to a flat tone.

### {number}-3 NIGHT INT. Dorm Laundry Room / 夜内 宿舍洗衣房

- 场景目标：lock the proof before Hale House buries it.
- 场景状态差量：Ava gains proof but triggers a new threat.
- 可见后果：the cliffhanger points to {ep['hook']}.

人物：Ava Reed / June Park / Veronica Hale

△ Washers spin behind Ava as June copies the file onto two cheap drives.
June Park: This is messy, but it's real.（证据不完整但真。）
Ava Reed: Real is enough for tonight.（先活过今晚。）
△ Ava's phone lights up with a call from Veronica.
Veronica Hale: You don't know what you opened.（反派威胁。）
Ava Reed: I opened the thing you locked.（Ava回击。）
△ June freezes when the hallway lights go out one by one.
June Park: Someone's outside.（危险靠近。）
Ava Reed: Then we stop whispering.（她选择公开。）
Veronica Hale: Last chance, sweetheart.（假温柔压迫。）
SFX：A dryer door slams by itself.
△ Ava hits record and says Veronica's name into the dark room.

## 本集回填

- 新增悬念：{ep['hook']}。
- 已兑现悬念：{ep['asset']} points to {ep['secret']}。
- 关系变化：June becomes Ava's public-risk ally.
- 资产变化：{ep['asset']} enters the evidence chain.
- 下一集必须承接：Ava responds to {ep['hook']}。

【{title}完】
"""


def common_qc(project_name: str, market: str) -> str:
    return f"""# {project_name} 质检检查点

## 全局问题追踪表

| ID | 日期 | 任务编号 | 阶段 | 复检方式 | 检查对象 | 等级 | 问题摘要 | 状态 | 必改时点 |
|----|------|---------|------|---------|---------|------|---------|------|---------|
| QC-001 | {GENERATED_AT} | T10 | 大纲质检 | dogfood-simulated | 分集大纲.md | P1 | EP011-020 回报类型重复，证据推进过密 | 已修复 | 剧本前 |
| QC-002 | {GENERATED_AT} | T14 | 剧本质检 | dogfood-simulated | EP021-030 | P1 | 尾钩连续使用“证人改口”，拉力趋同 | 已修复 | 下一批前 |
| QC-003 | {GENERATED_AT} | T15 | 全剧复核 | dogfood-simulated | EP001-EP060 | P2 | 个别场景复用偏高，AI 视觉变化不足 | 接受风险 | production-enhanced |

## {GENERATED_AT} /dogfood-自动流程说明

- 检查对象：{project_name}
- 检查范围：立项、策划、60 集大纲、60 集场次执行稿、交付前状态
- 任务编号：`T01-T18`
- 当前阶段：交付整合
- 复检方式：`dogfood-simulated`（端到端测试模拟；不是 production clean-context）
- 结论：通过 dogfood 验证，正式生产仍需新上下文独立复检
- 是否允许进入下一步：dogfood 测试允许；真实项目需按 references/18 重做 clean-context
- P0：无
- P1：已模拟回退修复 QC-001 / QC-002
- P2：视觉复用偏高，保留为 AI 视觉一致性策略
- 状态回写：
  - `currentStep`：交付整合
  - `lastQcStep`：交付质检
  - `lastIndependentReviewMode`：dogfood-simulated
  - `qcStatus`：dogfood 写入已通过，用于测试交付脚本
  - `changeControl`：已模拟开启并闭环一次上游回退
- 下一步：运行 check_episode.py 与 build_full_script.py

## 模拟回退记录

1. 策划结构回退：分集大纲中段连续使用相同证据回报，已把 EP016-018 / EP026-028 改成公开听证、切流、执行程序三类不同回报。
2. 剧本批次回退：EP021-030 尾钩重复“证人改口”，已拆成文件多页、对手报警、同盟反证、匿名坐标等不同钩子。
3. 交付前复核：{market}项目保留高复用场景策略，原因是 60 集 AI 竖屏剧优先稳角色和空间一致性。
"""


def cn_project() -> None:
    slug = "dogfood-cn-ruins-court-60"
    project = PROJECTS_DIR / slug
    if project.exists():
        raise SystemExit(f"Refuse to overwrite existing project: {project}")

    project_name = "她在废墟上开庭"
    outline_rows, outline_details = cn_outline_entries()

    write(project / "项目状态.json", project_state("standard"))
    write(
        project / "00-立项" / "项目简报.md",
        f"""# 项目简报

- 项目名：{project_name}
- 发行平台：抖音
- 目标市场：国内
- 总集数：60
- 单集时长：60-90 秒
- 内容形态：AI漫剧
- 商业化模式：商业化后置
- 目标观众：18-35 岁女性向都市爽剧观众，偏好现实压迫、公开反击、法律/商战清算。
- AI 制作口径：高复用城市空间，重证据、对峙、公开场；群像和公开场必须拆清视觉锚点和行动顺序。
- 确认记录：dogfood 自动测试假定用户已确认方向，用于验证完整流程。
""",
    )
    write(
        project / "00-立项" / "锁题摘要.md",
        f"""# 锁题摘要

- 项目名：{project_name}
- 发行平台：抖音
- 目标市场：国内
- 总集数：60
- 一句话题眼：父亲被城改黑账逼死后，女儿把每一份封口协议都变成公开审判。
- 核心卖点：现实机构压迫 + 女性克制反击 + 证据链逐集升级。
- 连载引擎一句话：每 10 集打开一层城改黑账，每层都让江闻雪从受害者更接近公开清算者。
- 核心压迫来源：荣曜集团用赔偿协议、老赖标签、切流、公证漏洞和执行程序压住受害者。
- 阶段回报节奏：EP001-010 拒签立誓；EP011-020 入局取证；EP021-030 身份翻面；EP031-045 公开清算；EP046-060 终局开庭。
- 不做项：不写超纲司法神话，不把复仇写成私刑，不靠豪车奢侈品撑爽点。
""",
    )
    write(
        project / "01-策划" / "项目设定.md",
        f"""# 项目设定

## 一、市场与组合

- 一句话题眼：父亲被城改黑账逼死后，女儿把封口协议变成公开审判。 [MUST]
- 发行平台：抖音。 [MUST]
- 目标市场：国内。 [MUST]
- 目标观众：抖音国内女性向现实复仇观众。 [MUST]
- 题材类型组合：都市复仇 / 法律商战 / 家族旧案。 [SHOULD]
- 选题策略：主流稳态 + AI-native 视觉型。 [MUST]
- 目标市场原生承诺：压迫来自城改、赔偿协议、老赖标签、直播切流和执行程序。 [MUST]
- 母体来源市场：无母体。 [MUST]

## 二、故事引擎

- 观众为什么点开：普通女孩在父亲追悼会拒签封口协议，当场反念旧合同。 [MUST]
- 连载引擎一句话：每 10 集拆一层荣曜集团黑账。 [MUST]
- 核心压迫来源：荣曜集团用制度和舆论压迫受害者家属。 [MUST]
- 压迫→爽点映射：每次对手用制度堵路，江闻雪就把同一制度变成证据出口。 [MUST]
- 观众为什么追：EP003 看到第一份假验收，EP010 看到第一轮公开反击，EP030 看到母亲旧案翻面，EP060 看到终局开庭。 [MUST]
- 阶段回报节奏：10 集一层证据，20 集一层身份，45 集公开清算，60 集终局闭环。 [MUST]

## 三、AI 制作口径

- AI 漫剧风格：冷色都市、文件证据、会议室对峙、雨夜楼道。 [MUST]
- 高复用资产策略：调解室 / 老楼 / 律所 / 荣曜会议室 / 听证厅循环复用。 [MUST]
- 下游镜头接口口径：群像大场面必须拆成近景、道具、灯光和文件推进。 [MUST]
- 禁止跑偏项：不写玄学开挂，不写无证私刑。 [SHOULD]

## 四、资产与制作

| 类型 | 名称 | 叙事功能 | 视觉记忆点 | 复用方式 |
| --- | --- | --- | --- | --- |
| 常驻场景 | 城改调解室 | 压迫与签字 | 红章、长桌、玻璃门 | 多批对峙 |
| 常驻场景 | 梁策律所 | 证据整理 | 扫描仪、旧案墙 | 每批复盘 |
| 核心道具 | 旧补充协议 | 第一证据 | 撕裂边角、蓝色印章 | 多次升级 |

## 五、市场本地化锚点

- 题材原生压迫机构 / 道具：城改、赔偿协议、老赖标签、执行程序、直播切流。 [MUST]
- 主流爽点 / 价值观弧光：公开清算、寒门反击、证据说话。 [MUST]
- 价值观红线规避：不美化私刑，不承诺超现实司法结果。 [MUST]
- 地域 / 阶层锚点：新一线城改、老楼业主、集团公关。 [SHOULD]
""",
    )
    write(
        project / "01-策划" / "世界观设定.md",
        """# 世界观设定

## 一、现实规则

- 城改项目靠验收、补充协议、公示流程和执行程序推进。
- 荣曜集团的压迫不靠黑帮，而靠合同、舆论、公章和时间差。
- 江闻雪每次反击都必须拿到可见证据，不能靠口号。

## 二、代价

- 公开一份证据，就会失去一层安全空间。
- 保护一个证人，就会暴露一个亲友软肋。
- 每次推进程序，都会触发荣曜集团的反向程序。
""",
    )
    write(
        project / "01-策划" / "人物小传.md",
        """# 人物小传

## 一、角色关系总览

- 主关系一句话：江闻雪和梁策从互不信任的证据同盟变成共同开庭的战友。 [MUST]
- 主角压力来源：父亲旧案、母亲失踪、债务标签、集团公关。 [MUST]
- 核心对手压迫方式：周曼丽用协议、公示、舆论和证人调包压回去。 [MUST]
- 核心关系位拉扯方式：梁策怕她越界，江闻雪怕他只求稳。 [MUST]

## 二、主要角色

### 江闻雪

- 剧情功能：主角，证据链推动者。 [MUST]
- 身份与处境：前法务助理，父亲事故后背债。 [MUST]
- 想要什么：证明父亲不是老赖，公开荣曜黑账。 [MUST]
- 被谁/什么压迫：荣曜集团、债务标签、执行程序。 [MUST]
- 反击方式：把对手文件变成公开证据。 [MUST]
- 与主线的关系：每一集由她推动证据升级。 [MUST]
- 外形关键词：黑短发、旧风衣、文件袋。 [SHOULD]
- 固定识别锚点：蓝色旧协议夹。 [SHOULD]
- 首次出场必须交代的信息：追悼会拒签封口协议。 [SHOULD]
- 终局状态：在庭审上完成公开清算。 [MUST]

### 梁策

- 剧情功能：律师同盟，程序边界提醒者。 [MUST]
- 身份与处境：被律所边缘化的青年律师。 [MUST]
- 想要什么：赢一个干净的案子。 [MUST]
- 被谁/什么压迫：律所利益和职业风险。 [MUST]
- 反击方式：用程序把江闻雪的证据变成可提交材料。 [MUST]
- 与主线的关系：把情绪反击转成法律动作。 [MUST]
- 终局状态：出庭代理再审。 [MUST]

### 周曼丽

- 剧情功能：核心反派，荣曜集团公关与旧案掩盖者。 [MUST]
- 身份与处境：荣曜副总，掌握城改公关线。 [MUST]
- 想要什么：压住旧案，保住上市审查。 [MUST]
- 被谁/什么压迫：董事会和旧账册。 [MUST]
- 反击方式：切流、换证人、造舆论。 [MUST]
- 与主线的关系：每阶段制造新制度压迫。 [MUST]
- 终局状态：在庭审前夜被原始账册锁死。 [MUST]
""",
    )
    write(
        project / "01-策划" / "故事梗概.md",
        f"""# 故事梗概

- 类型与题眼：都市现实复仇，女儿把封口协议变成公开审判。 [MUST]
- 主角与开局困境：江闻雪在父亲追悼会上被逼签赔偿协议。 [MUST]
- 主目标：证明父亲旧案背后是荣曜集团城改黑账。 [MUST]
- 主要对手与核心对抗：周曼丽用制度和舆论压人，江闻雪用证据和公开程序反击。 [MUST]
- 主卖点与续看理由：每 10 集拆开一层黑账，每层都有可见证据和公开反击。 [MUST]
- 中段升级：母亲失踪线索与城改验收造假合流。 [MUST]
- 终局兑现：江闻雪把所有封口材料带上庭，完成公开清算。 [MUST]
""",
    )
    write(
        project / "01-策划" / "故事大纲.md",
        """# 故事大纲

- 全剧升级链一句话：拒签封口 -> 入局取证 -> 母亲旧案翻面 -> 公开听证 -> 低谷护证 -> 终局开庭。 [MUST]

| 阶段 | 阶段目标 | 主要阻力 | 推进方式 | 关键翻面 | 阶段回报 | 接口遗留 |
| --- | --- | --- | --- | --- | --- | --- |
| 开篇与卷入 | 拒签并找到第一份旧协议 | 荣曜封口和债务标签 | 追悼会反击、老楼取证 | 父亲不是事故边缘人 | 第一证据成立 | 旧协议是谁补的 |
| 第一阶段推进 | 进入调解和执行程序 | 律师函、切流、公示时间差 | 找业主和验收记录 | 证据链指向荣曜内部 | 公开反击第一次成立 | 内鬼是谁 |
| 中段升级 | 母亲线索浮出 | 伪证人、旧公证缺页 | 找录音、公证员、旧照片 | 母亲曾掌握原始账册 | 身份与旧案合流 | 原始账册在哪里 |
| 后段失控 | 推动公开听证 | 行政投诉反噬、证人遇险 | 护证人、公开程序 | 周曼丽亲自下场 | 听证进入终局 | 董事会保护伞 |
| 结局收束 | 申请再审并开庭 | 终审前夜威胁 | 原始账册 + 多证人闭环 | 父亲死因被公开 | 终局清算 | 剧终 |
""",
    )
    write(
        project / "01-策划" / "故事节拍表.md",
        """# 故事节拍表

| 节拍 | 集数 | 事件 | 观众回报 |
| --- | --- | --- | --- |
| 引爆事件 | EP001 | 追悼会拒签封口协议 | 主角站起来 |
| 第一次翻面 | EP010 | 第一份假验收公开 | 反击成立 |
| 中点翻面 | EP030 | 母亲线索指向原始账册 | 旧案变大案 |
| 重大揭露 | EP045 | 听证会上保护伞露出 | 反派失控 |
| 最低谷 | EP050 | 证人被转移，梁策被停职 | 全线失守 |
| 终局对决 | EP060 | 原始账册进入庭审 | 公开清算 |
""",
    )
    write(
        project / "01-策划" / "阶段大纲.md",
        """# 阶段大纲

| 阶段 | 集数范围 | 阶段任务 | 本阶段主导动词 | 阶段高潮 | 阶段尾钩 | 传播级高光 | 高复用场景 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开篇 | EP001-010 | 拒签并立证 | 反签 | 假验收公开 | 内鬼露面 | 追悼会反念协议 | 调解室 |
| 中段一 | EP011-030 | 入局取证并身份翻面 | 截证 | 母亲线索出现 | 原始账册存在 | 直播被切仍读证据 | 律所 |
| 中段二 | EP031-045 | 公开听证 | 逼公开 | 保护伞露出 | 证人消失 | 听证厅沉默十秒 | 听证厅 |
| 终局 | EP046-060 | 护证并开庭 | 开庭 | 原始账册提交 | 剧终 | 庭上逐页念封口协议 | 法庭 |
""",
    )
    write(
        project / "01-策划" / "分集大纲.md",
        f"""# 分集大纲

## 一、分集总览

| 集数 | 一句话剧情 | 本集观众一句话 | 本集爆点 | 本集回报类型 | 本集主要回报 | 结尾钩子 |
| --- | --- | --- | --- | --- | --- | --- |
{outline_rows}

## 二、单集条目

{outline_details}
""",
    )

    for i in range(1, 61):
        write(project / "02-剧本" / f"第{i:03d}集.md", cn_episode(i))

    write(project / "90-内部工作稿" / "质检检查点.md", common_qc(project_name, "抖音 / 国内"))
    write(project / "90-内部工作稿" / "分集追踪.md", "# 分集追踪\n\n- 已完成范围：EP001-EP060\n- 当前风险：中段证据回报需要在正式复检中重点抽查。\n")


def us_project() -> None:
    slug = "dogfood-us-nda-heiress-60"
    project = PROJECTS_DIR / slug
    if project.exists():
        raise SystemExit(f"Refuse to overwrite existing project: {project}")

    project_name = "The NDA Heiress"
    outline_rows, outline_details = us_outline_entries()

    write(project / "项目状态.json", project_state("production-enhanced"))
    write(
        project / "00-立项" / "项目简报.md",
        f"""# 项目简报

- 项目名：{project_name}
- 发行平台：TikTok
- 目标市场：美国英语首版
- 总集数：60
- 单集时长：45-75 秒
- 内容形态：AI漫剧
- 商业化模式：商业化后置
- 目标观众：18-34 岁 TikTok melodrama / revenge / hidden-heir 观众。
- AI 制作口径：美国英语首版，策划中文，正文英文对白加中文注释；公开场和 boardroom scene 拆清视觉锚点。
- 确认记录：dogfood 自动测试假定用户已确认方向，用于验证完整流程。
""",
    )
    write(
        project / "00-立项" / "锁题摘要.md",
        f"""# 锁题摘要

- 项目名：{project_name}
- 发行平台：TikTok
- 目标市场：美国英语首版
- 总集数：60
- 一句话题眼：A broke intern refuses an NDA and proves she is the hidden heir of the media family trying to erase her.
- 核心卖点：hidden heiress + NDA pressure + campus/public cancellation + trust-board revenge。
- 连载引擎一句话：Ava 每 10 集拆开一层 Hale 家族的法律封口和身份骗局。
- 核心压迫来源：NDA、restraining order、shadow ban、trust board、donor politics。
- 阶段回报节奏：EP001-010 refuse NDA；EP011-020 enter Hale House；EP021-030 identity turn；EP031-045 board hearing；EP046-060 final trust vote。
- 不做项：不写中式保安拦门，不写 How dare you 式翻译腔，不把 American Dream 写成空标签。
""",
    )
    write(
        project / "01-策划" / "项目设定.md",
        """# 项目设定

## 一、市场与组合

- 一句话题眼：A broke intern refuses an NDA and becomes the only person who can break Hale House. [MUST]
- 发行平台：TikTok。 [MUST]
- 目标市场：美国英语首版。 [MUST]
- 目标观众：TikTok 美国英语女性向 revenge / hidden-heir 观众。 [MUST]
- 题材类型组合：Hidden heiress / corporate family / campus cancellation。 [SHOULD]
- 选题策略：主流稳态 + 类型微创新。 [MUST]
- 目标市场原生承诺：压迫来自 NDA、trust board、restraining order、shadow ban 和 donor politics。 [MUST]
- 母体来源市场：无母体。 [MUST]

## 二、故事引擎

- 观众为什么点开：Ava 在 trust office 当场拒签 NDA。 [MUST]
- 连载引擎一句话：每 10 集 Ava 破解一层 Hale 家族封口系统。 [MUST]
- 核心压迫来源：Veronica 用 NDA、board vote 和舆论取消压 Ava。 [MUST]
- 压迫→爽点映射：每个法律/名誉压迫都被 Ava 反用成公开证据。 [MUST]
- 观众为什么追：身份、继承、背叛和公开反击逐层升级。 [MUST]
- 阶段回报节奏：10 集一个 public proof，30 集身份翻面，60 集 trust vote 终局。 [MUST]

## 三、AI 制作口径

- AI 漫剧风格：sleek campus noir, glass offices, laundry room secrets, boardroom confrontation. [MUST]
- 高复用资产策略：Trust office / campus steps / dorm laundry / Hale boardroom / hearing room. [MUST]
- 下游镜头接口口径：大型派对和群像必须拆成近景、文件、手机和门口对峙推进。 [MUST]
- 禁止跑偏项：不写中式威胁句，不靠暴力私刑推进。 [SHOULD]

## 四、资产与制作

| 类型 | 名称 | 叙事功能 | 视觉记忆点 | 复用方式 |
| --- | --- | --- | --- | --- |
| 常驻场景 | Trust Office | NDA pressure | glass table, folders, cold light | legal pressure scenes |
| 常驻场景 | Dorm Laundry | secret copying | machines, cheap USB drives | ally scenes |
| 核心道具 | Unsigned NDA Rider | first proof | blue sticky note, missing signature | evidence chain |

## 五、市场本地化锚点

- 题材原生压迫机构 / 道具：NDA、trust board、restraining order、shadow ban、donor list。 [MUST]
- 主流爽点 / 价值观弧光：Underdog, reinvention, found family, public accountability。 [MUST]
- 价值观红线规避：不美化 gaslighting / love bombing / DV。 [MUST]
- 地域 / 阶层锚点：East Coast private campus, legacy donor family, media trust。 [SHOULD]
- 节日 / 季节钩点：Thanksgiving board dinner 可用于 EP041-045。 [MAY，海外项目或节日钩点项目必填]
""",
    )
    write(
        project / "01-策划" / "世界观设定.md",
        """# 世界观设定

## 一、现实规则

- Hale House 是家族媒体信托，靠 trust board vote 决定继承和控制权。
- NDA 是压迫工具，不是万能魔法；每次出现都必须有签署对象、利益和代价。
- Ava 的反击必须把私人受害转成 public proof。

## 二、代价

- 公开证据会带来 shadow ban、campus discipline 和 donor pressure。
- 每推进一层身份证据，Ava 都会失去一层安全关系。
""",
    )
    write(
        project / "01-策划" / "人物小传.md",
        """# 人物小传

## 一、角色关系总览

- 主关系一句话：Ava 和 Mason 从互相隐瞒的继承关系变成共同破局的危险同盟。 [MUST]
- 主角压力来源：NDA、贫困、身份抹除、public shame。 [MUST]
- 核心对手压迫方式：Veronica 用 trust board、media narrative 和 legal threat 压回去。 [MUST]
- 核心关系位拉扯方式：Mason 想 quietly fix，Ava 必须 publicly expose。 [MUST]

## 二、主要角色

### Ava Reed

- 剧情功能：主角，hidden heiress 与 public proof 推动者。 [MUST]
- 身份与处境：贫困实习生，被 Hale House 用 NDA 封口。 [MUST]
- 想要什么：证明母亲和自己被 Hale family 抹除。 [MUST]
- 被谁/什么压迫：Veronica、trust board、campus discipline、shadow ban。 [MUST]
- 反击方式：把私人证据变成公开证据。 [MUST]
- 与主线的关系：所有身份证据由她推进。 [MUST]
- 外形关键词：dark ponytail, thrift blazer, cracked phone。 [SHOULD]
- 固定识别锚点：cheap USB drive on a keyring。 [SHOULD]
- 首次出场必须交代的信息：拒签 NDA。 [SHOULD]
- 终局状态：赢下 trust vote 但拒绝成为 Veronica。 [MUST]

### Mason Hale

- 剧情功能：关系位与内部通道。 [MUST]
- 身份与处境：Hale heir on paper, privately doubts the family story。 [MUST]
- 想要什么：keep control without destroying the family。 [MUST]
- 被谁/什么压迫：Veronica and the board。 [MUST]
- 反击方式：leaks access, then testifies。 [MUST]
- 与主线的关系：把 Ava 带进 Hale House。 [MUST]
- 终局状态：公开站到 Ava 一边。 [MUST]

### Veronica Hale

- 剧情功能：核心反派。 [MUST]
- 身份与处境：Hale House 控制者。 [MUST]
- 想要什么：protect the trust vote and erase Ava's claim。 [MUST]
- 被谁/什么压迫：old ledger and donor exposure。 [MUST]
- 反击方式：NDA, smear campaign, board pressure。 [MUST]
- 与主线的关系：每阶段制造制度压迫。 [MUST]
- 终局状态：最后一个 NDA 反噬。 [MUST]
""",
    )
    write(
        project / "01-策划" / "故事梗概.md",
        """# 故事梗概

- 类型与题眼：Hidden heiress revenge about refusing an NDA. [MUST]
- 主角与开局困境：Ava is a broke intern pressured to sign away her claim. [MUST]
- 主目标：prove she is the erased Hale heir and expose the trust cover-up. [MUST]
- 主要对手与核心对抗：Veronica controls money, law, and media; Ava controls public proof. [MUST]
- 主卖点与续看理由：every ten episodes breaks one legal/social lock. [MUST]
- 中段升级：Ava's birth record and her mother's cover-up join the inheritance plot. [MUST]
- 终局兑现：Ava breaks the final trust vote in front of the board. [MUST]
""",
    )
    write(
        project / "01-策划" / "故事大纲.md",
        """# 故事大纲

- 全剧升级链一句话：refuse NDA -> enter Hale House -> identity turn -> board hearing -> protect whistleblower -> final trust vote. [MUST]

| 阶段 | 阶段目标 | 主要阻力 | 推进方式 | 关键翻面 | 阶段回报 | 接口遗留 |
| --- | --- | --- | --- | --- | --- | --- |
| Hook | Refuse NDA and find the first rider | Veronica's legal threat | public refusal and campus proof | Ava has a real claim | first proof | who hid the rider |
| Inside | Get access to Hale House | shadow ban and donor pressure | Mason access, June stream | logs show manipulation | public proof | who planted the witness |
| Identity | Prove birth and trust trail | sealed records | voicemail, clinic record | Ava's mother was erased | identity turn | ledger location |
| Public | Force a board hearing | cancellation campaign | donor list, board minutes | Veronica loses narrative | public hearing | whistleblower safety |
| Low Point | Protect whistleblower | betrayal and restraining order | cheap copies, public risk | Mason chooses Ava | ally payoff | final NDA |
| Final | Break the trust vote | last NDA and board threat | original ledger | trust cover-up exposed | final accountability | end |
""",
    )
    write(
        project / "01-策划" / "故事节拍表.md",
        """# 故事节拍表

| 节拍 | 集数 | 事件 | 观众回报 |
| --- | --- | --- | --- |
| 引爆事件 | EP001 | Ava refuses the NDA | underdog stands up |
| 第一次翻面 | EP010 | unsigned rider goes public | proof exists |
| 中点翻面 | EP030 | birth record links to trust | identity turn |
| 重大揭露 | EP045 | donor list exposes laundering | public pressure |
| 最低谷 | EP050 | June is threatened, Mason wavers | all seems lost |
| 终局对决 | EP060 | final board vote breaks | accountability |
""",
    )
    write(
        project / "01-策划" / "阶段大纲.md",
        """# 阶段大纲

| 阶段 | 集数范围 | 阶段任务 | 本阶段主导动词 | 阶段高潮 | 阶段尾钩 | 传播级高光 | 高复用场景 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hook | EP001-010 | refuse NDA | resist | rider goes public | witness recants | "That's not payment. That's a muzzle." | Trust Office |
| Inside | EP011-030 | enter system | expose | birth record appears | sealed voicemail | Ava keeps recording in the dark | Campus Steps |
| Public | EP031-045 | force hearing | confront | donor list drops | whistleblower vanishes | board room silence | Hale Boardroom |
| Final | EP046-060 | break vote | testify | ledger submitted | end | Ava refuses Veronica's chair | Hearing Room |
""",
    )
    write(
        project / "01-策划" / "分集大纲.md",
        f"""# 分集大纲

## 一、分集总览

| 集数 | 一句话剧情 | 本集观众一句话 | 本集爆点 | 本集回报类型 | 本集主要回报 | 结尾钩子 |
| --- | --- | --- | --- | --- | --- | --- |
{outline_rows}

## 二、单集条目

{outline_details}
""",
    )

    for i in range(1, 61):
        write(project / "02-剧本" / f"EP{i:03d}.md", us_episode(i))

    write(project / "90-内部工作稿" / "质检检查点.md", common_qc(project_name, "TikTok / 美国英语首版"))
    write(project / "90-内部工作稿" / "分集追踪.md", "# 分集追踪\n\n- 已完成范围：EP001-EP060\n- 当前风险：英文 register 和中文注释需要正式复检重点抽查。\n")
    write(
        project / "03-交付" / "制作理解稿.md",
        """# 制作理解稿

## 一、项目概览

- 项目名：The NDA Heiress
- 发行平台：TikTok
- 目标市场：美国英语首版
- 内容形态：AI漫剧
- AI 风格：sleek campus noir
- 规格：60 x 45-75s
- 改编来源：原创

## 二、这个故事到底在讲什么

Ava 不是要当富家女，她要证明 Hale House 用法律文件和媒体叙事抹掉了她和母亲。

## 三、核心情绪点

- 主情绪：被羞辱后的公开反击
- 次情绪：found family
- 开篇阶段核心回报：拒签 NDA
- 整季最重要的爽点/虐点：每一次封口都变成公开证据
""",
    )
    write(
        project / "03-交付" / "制作交付参数表.md",
        """# 制作交付参数表

## 一、版本来源

- 项目名：The NDA Heiress
- 发行平台：TikTok
- 目标市场：美国英语首版
- 适用交付对象：AI 漫剧分镜 / 视频 / 配音前置整理
- 参数来源文档：01-策划 + 02-剧本
- 参数版本日期：dogfood
- 本表整理日期：dogfood

## 二、规格参数

- 画幅比例：9:16
- 单集目标时长：45-75 秒
- 总集数：60

## 三、语言与本地化

- 对白语言：American English
- 配音口音：General American
- 字幕语言：English
- 角色命名格式：English full name first appearance, first name after
- 海外交付标点默认：英文标点（ASCII）
""",
    )
    write(
        project / "03-交付" / "海外制作版分场表.md",
        """# 海外制作版分场表

## 项目信息

- 项目名：The NDA Heiress
- 发行平台：TikTok
- 目标市场：美国英语首版
- 交付范围：EP001-EP060
- 台词语言：英文（source of truth = `02-剧本/EPXXX.md`）
- 是否另附中文备注：否
- 标点规则：英文标点（ASCII）

## source-of-truth 提醒

- 本表为 dogfood 占位版，真实制作交付需从已通过复检的 EP 文件抽取台词。
- 修改台词必须回到 `02-剧本/EPXXX.md` 改 source。
""",
    )


def dogfood_report() -> None:
    write(
        PROJECTS_DIR / "dogfood-short-drama-scriptwriter-report.md",
        f"""# short-drama-scriptwriter Dogfood Report

- 生成时间：{GENERATED_AT}
- 国内项目：`projects/dogfood-cn-ruins-court-60`
- 美国英语项目：`projects/dogfood-us-nda-heiress-60`
- 测试目标：模拟用户从立项、策划、分集大纲、分批正文、回退复检到交付整合的完整使用过程。

## 执行口径

- 两个项目都生成 60 集正式分集大纲和 60 个场次执行稿。
- 国内项目按 standard 交付；美国英语出海项目按 production-enhanced 交付并预置增强包文件。
- 质检记录使用 `dogfood-simulated`，用于测试流程和脚本，不冒充 production clean-context。

## 人类编剧式模拟行为

1. 先锁发行平台、目标市场、受众、商业化状态和 AI 制作口径。
2. 再做项目设定、世界观、人物、梗概、大纲、节拍和阶段大纲。
3. 生成全量分集大纲后，模拟发现中段回报重复并回退。
4. 分 6 批写正文，每批 10 集；模拟发现尾钩重复并回退修正。
5. 交付前记录 T15 全剧复核状态，用于测试 build_full_script.py 的新门禁。

## 已观察到的 skill 设计问题

- 正式 clean-context 放行与“用户希望一口气自动完成”的体验冲突仍存在；建议未来增加 `dogfood / draft / production` 三档门禁模式。
- production-enhanced 文件目前需要人工/模型先生成，汇总脚本只校验存在，不会从正文自动抽取分场表。
- 60 集全量生成会让正式产物很大，后续可以考虑增加批次生成器或项目初始化脚本，减少手工文件操作。
""",
    )


def main() -> int:
    PROJECTS_DIR.mkdir(exist_ok=True)
    cn_project()
    us_project()
    dogfood_report()
    print("Generated dogfood projects:")
    print("  - projects/dogfood-cn-ruins-court-60")
    print("  - projects/dogfood-us-nda-heiress-60")
    print("  - projects/dogfood-short-drama-scriptwriter-report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
