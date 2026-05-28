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

#let statute-style(body) = {
  set page(
    paper: "a4",
    margin: (
      x: 3cm,
      y: 2.5cm,
    ),
  )

  set text(
    font: (
      (name: "Times New Roman", covers: "latin-in-cjk"),
      "Noto Serif TC",
    ),
    size: 12pt,
    lang: "zh",
    region: "TW",
    top-edge: "ascender",
    bottom-edge: "descender"
  )

  // 文件標題
  show heading.where(level: 1): it => {
    align(center)[
      #text(18pt, weight: "bold")[
        #it.body
      ]
    ]
  }

  // 章
  show heading.where(level: 2): it => {
    context {
      let n = chapter-counter.get().first() + 1

      chapter-counter.step()
      v(2em)

      align(center)[
        #text(14pt, weight: "semibold")[
          第#to-cjk(n)章　#it.body
        ]
      ]
    }
  }

  body
}

// 條（建議使用 #article[...]，可同條換行/分段）
#let article(body) = {
  context {
    let n = article-counter.get().first() + 1
    article-counter.step()
    v(1.5em)
    block[
      #text(weight: "bold")[第#to-cjk(n)條]
      #pad(left: 1em)[#body]
    ]
  }
}

#let para(body) = {
  par(
    leading: 0.7em, spacing: 1em
  )[#body]
}

#let subpara(body) = {
  par(leading: 0.7em, spacing: 1em, hanging-indent: 2em)[#body]
}