# Handmade Story Visuals

一套原创的 Codex Skill，用来把故事、场景、知识讲解和连续叙事转换成稳定、可复用的手作视觉提示词包。

它不绑定特定图片模型，也不模仿具体画师、工作室或受保护角色。Skill 会从内容中选择合适的手绘媒介，保留用户指定的画面文字和人物设定，并同时输出正向提示词、负向提示词与检查项。

## 主要能力

- 根据故事内容自动推荐手作视觉风格，也支持手动指定。
- 内置 10 种独立设计的风格配方，涵盖铅笔、水粉、拼贴、粉笔、蜡彩和叠纸等媒介。
- 原样保留画面中必须出现的文字，不翻译、不润色、不擅自添加标点。
- 锁定人物外貌、服装、道具、色彩与场景规则，方便制作连续系列。
- 支持横版、竖版等用户提供的画面比例。
- 可输出适合阅读的文本格式，也可输出供工作流调用的 JSON。
- 使用确定性脚本完成风格选择和提示词组装，便于复现和测试。

## 内置风格

| ID | 风格名称 | Slug | 适合内容 |
| --- | --- | --- | --- |
| S01 | 铅笔留白日记 | `graphite-moment` | 克制情绪、回忆、安静瞬间 |
| S02 | 街角水粉叙事 | `street-corner-gouache` | 街巷、雨夜、人与环境 |
| S03 | 一线寓言 | `single-line-fable` | 因果关系、哲理与视觉隐喻 |
| S04 | 蜡彩窗光 | `windowlight-wax` | 温暖室内、亲密关系、童真故事 |
| S05 | 旧票根拼贴 | `ticket-stub-collage` | 旅行、书信、记忆与真实小物 |
| S06 | 深夜粉笔剧场 | `midnight-chalk-stage` | 夜间故事、想象与轻松讲解 |
| S07 | 黑金寓言剪影 | `black-gold-parable` | 哲理转折、传统智慧、庄重叙事 |
| S08 | 叠纸小剧场 | `layered-paper-theatre` | 分层场景、童话与立体叙事 |
| S09 | 方格本铅笔讲解 | `notebook-explainer` | 步骤拆解、知识说明与分镜 |
| S10 | 暖邮片绘本 | `postcard-storybook` | 日常故事、温暖片段与通用场景 |

使用 `auto` 时，编译器会根据主题和叙事重点进行可解释的关键词匹配；没有匹配结果时使用暖邮片绘本作为默认风格。

## 安装

将仓库克隆到 Codex 的 Skills 目录：

```bash
git clone https://github.com/elliotwoo98-dotcom/handmade-story-visuals.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/handmade-story-visuals"
```

重新启动 Codex 或开启一个新任务后即可使用。

## 在 Codex 中使用

可以直接描述目标，不需要记命令。例如：

```text
把“雨夜里，女孩把唯一的伞递给陌生老人”做成 9:16 手绘故事画面。
画面必须出现“把伞留给更需要的人”，人物固定为短发、黄色雨衣、红色布鞋。
```

也可以指定风格或要求连续性：

```text
使用“黑金寓言剪影”，为这段哲理故事生成三张连续画面的提示词包。
三张图保持同一人物、同一服装、同一画面比例，不要出现任何文字。
```

默认交付的是提示词包。只有用户明确要求生成图片，并且当前环境提供图片工具时，才会继续生成图像。

## 直接使用编译器

生成文本格式提示词包：

```bash
python3 scripts/compile_prompt.py \
  --subject "雨夜里，女孩把唯一的伞递给陌生老人" \
  --intent "突出善意发生前后的情绪变化" \
  --style auto \
  --aspect 9:16 \
  --text "把伞留给更需要的人" \
  --character-lock "女孩：短发、黄色雨衣、红色布鞋"
```

生成结构化 JSON：

```bash
python3 scripts/compile_prompt.py \
  --subject "同一位女孩第二天回到公交站" \
  --style graphite-moment \
  --aspect 9:16 \
  --character-lock "女孩：短发、黄色雨衣、红色布鞋" \
  --series-context "沿用上一张的雨夜城市、人物比例与低饱和配色" \
  --no-text \
  --format json
```

查看全部风格：

```bash
python3 scripts/compile_prompt.py --list-styles
```

## 输出内容

每个提示词包包含：

- 原始输入与连续性锁定信息
- 选中的风格和选择依据
- 正向提示词
- 独立的负向提示词
- 画面文字与生成前检查项

JSON 输出结构由 [`references/output-schema.json`](references/output-schema.json) 定义。

## 项目结构

```text
handmade-story-visuals/
├── README.md                      # 项目介绍、安装和使用说明
├── SKILL.md                       # Skill 入口与核心工作流
├── agents/openai.yaml             # Codex 界面元数据
├── references/
│   ├── styles.json                # 风格目录、别名与选择关键词
│   ├── workflow.md                # 连续性、文字与交付检查
│   └── output-schema.json         # JSON 输出约定
├── scripts/compile_prompt.py       # 确定性提示词编译器
└── tests/test_compile_prompt.py    # 单元测试
```

## 测试与验证

项目只使用 Python 标准库。运行测试：

```bash
python3 -m unittest discover -s tests -v
```

当前测试覆盖风格解析、自动推荐、默认回退、精确文字保留、无文字约束、连续性锁定、输出结构和命令行行为。

## 设计原则

- 先忠实表达故事，再选择视觉媒介。
- 用户给出的可见文字与人物锁定信息不可擅自改写。
- 风格描述使用可观察的线条、材质、色彩和构图特征。
- 不使用画师、工作室、影视品牌或受保护角色名称来要求精确模仿。
- 图片中的精确文字必须在生成后复核；必要时单独处理文字层。

## 版权说明

本仓库中的 Skill、风格配方、工作流和脚本均为独立原创内容。本项目采用 [MIT License](LICENSE)，允许在保留版权与许可声明的前提下使用、修改、分发和商用。
