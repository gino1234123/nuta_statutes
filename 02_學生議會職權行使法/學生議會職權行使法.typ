#set page(
  paper: "a4",
  margin: (
    x: 3cm,
    y: 2.5cm,
  ),
)

#set text(
  font: (
  (name: "Times New Roman", covers: "latin-in-cjk"),
  "TW-Kai"),
  size: 12pt,
  lang: "zh",
  region: "TW"
)


#let chapter-counter = counter("chapter")
#let article-counter = counter("article")

// 阿拉伯數字轉中文小寫（1..9999）
#let to-cjk(n) = {
  let d = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")
  if n <= 0 {
    "零"
  } else if n < 10 {
    d.at(n)
  } else if n < 100 {
    let t = calc.floor(n / 10)
    let o = calc.rem(n, 10)
    if t == 1 {
      if o == 0 { "十" } else { "十" + d.at(o) }
    } else {
      if o == 0 { d.at(t) + "十" } else { d.at(t) + "十" + d.at(o) }
    }
  } else if n < 1000 {
    let h = calc.floor(n / 100)
    let r = calc.rem(n, 100)
    if r == 0 {
      d.at(h) + "百"
    } else if r < 10 {
      d.at(h) + "百零" + d.at(r)
    } else {
      d.at(h) + "百" + to-cjk(r)
    }
  } else if n < 10000 {
    let th = calc.floor(n / 1000)
    let r = calc.rem(n, 1000)
    if r == 0 {
      d.at(th) + "千"
    } else if r < 100 {
      d.at(th) + "千零" + to-cjk(r)
    } else {
      d.at(th) + "千" + to-cjk(r)
    }
  } else {
    str(n)
  }
}

// 文件標題
#show heading.where(level: 1): it => {
  align(center)[
    #text(18pt, weight: "bold")[
      #it.body
    ]
  ]
}

// 章
#show heading.where(level: 2): it => {
  context {
    let n = chapter-counter.get().first() + 1

    chapter-counter.step()
    
    v(2em)

    align(center)[
      #text(14pt, weight: "bold")[
        第#to-cjk(n)章　#it.body
      ]
    ]

  }
}

// 條（建議使用 #article[...]，可同條換行/分段）
#let article(body) = {
  context {
    let n = article-counter.get().first() + 1
    article-counter.step()
    v(1.5em)
    block[
      #text[第#to-cjk(n)條]
      #par(hanging-indent: 1em, first-line-indent: 1em)[#body]
    ]
  }
}

= 國立臺灣藝術大學學生會學生議會職權行使法