# Tarot Card Set / 塔罗牌集合

`card_set.json` stores a complete 78-card tarot deck as an array of card objects.

`card_set.json` 以对象数组的形式存储完整的 78 张塔罗牌。

## Card Properties / 卡牌属性

| Property / 属性 | Type / 类型 | Meaning / 含义 |
| --- | --- | --- |
| `name` | string / 字符串 | The card's English name, such as `The Fool` or `Ace of Wands`. / 卡牌的英文名称，例如 `The Fool` 或 `Ace of Wands`。 |
| `arcana` | string / 字符串 | The card group: `Major` for the 22 Major Arcana cards, or `Minor` for the 56 Minor Arcana cards. / 卡牌类别：`Major` 表示 22 张大阿卡纳，`Minor` 表示 56 张小阿卡纳。 |
| `suit` | string or `null` / 字符串或 `null` | The Minor Arcana suit: `Wands`, `Cups`, `Swords`, or `Pentacles`. Major Arcana cards use `null`. / 小阿卡纳花色：`Wands`（权杖）、`Cups`（圣杯）、`Swords`（宝剑）或 `Pentacles`（星币）。大阿卡纳使用 `null`。 |
| `number` | integer or `null` / 整数或 `null` | The card number. Major Arcana cards use `0` through `21`; numbered Minor Arcana cards use `1` through `10`; court cards use `null`. / 卡牌编号。大阿卡纳使用 `0` 到 `21`；小阿卡纳数字牌使用 `1` 到 `10`；宫廷牌使用 `null`。 |
| `rank` | string or `null` / 字符串或 `null` | The card rank. Numbered Minor Arcana cards use `Ace`, `Two`, through `Ten`; court cards use `Page`, `Knight`, `Queen`, or `King`; Major Arcana cards use `null`. / 卡牌等级。数字牌使用 `Ace` 到 `Ten`；宫廷牌使用 `Page`、`Knight`、`Queen` 或 `King`；大阿卡纳使用 `null`。 |
| `element` | string / 字符串 | The associated element: `Fire`, `Water`, `Air`, or `Earth`. / 对应元素：`Fire`（火）、`Water`（水）、`Air`（风）或 `Earth`（土）。 |
| `upright` | array of strings / 字符串数组 | Short keywords describing common meanings when the card is upright. / 描述卡牌正位常见含义的关键词。 |
| `reversed` | array of strings / 字符串数组 | Short keywords describing common meanings when the card is reversed. / 描述卡牌逆位常见含义的关键词。 |

## Structure / 数据结构

The top level is an array. The card name is stored in the `name` property rather than being used as an object key.

顶层数据是一个数组。卡牌名称存储在 `name` 属性中，而不是作为对象的键名：

```json
[
	{
		"name": "The Fool",
		"arcana": "Major",
		"suit": null,
		"number": 0,
		"rank": null,
		"element": "Air",
		"upright": ["beginnings", "freedom"],
		"reversed": ["recklessness", "hesitation"]
	}
]
```

## Card Groups / 卡牌分类

- **Major Arcana / 大阿卡纳：** 22 cards numbered from `0` to `21`; they do not have a suit or rank. / 共 22 张，编号为 `0` 到 `21`；没有花色和等级。
- **Minor Arcana / 小阿卡纳：** 56 cards divided into four suits. Each suit contains Ace through Ten plus Page, Knight, Queen, and King. / 共 56 张，分为四种花色；每种花色包含 Ace 到 Ten，以及 Page、Knight、Queen 和 King 四张宫廷牌。