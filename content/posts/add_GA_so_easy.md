+++
date = '2025-10-27T22:08:51-07:00'
draft = false
title = '三步驟在 Hugo 加 Google Analytics'
tags = ["hugo","blog"]
+++

- 版本： hugo v0.152.2
- submodules：啟用

這個版本有內建模板用於 Google Analytics 4。我們要做的就是: 1. 在 header 加入調用模板指令 2. 在 hugo.toml 啟用並且設置 tracking ID。 值得注意的是：在我的例子中，我是透過 submodules 套用別人的模板。 在不更改別人的模板情況下，我需要創建一個 header 副本來覆蓋現在有模板的 header。

## 實際操作

1. 在你的 hugo 跟資料夾，創建覆蓋用的資料夾。然後複製模板的 header 到這個新資料夾
```
mkdir -p layouts/partials
cp themes/mainroad/layouts/partials/header.html layouts/partials/
```

2. 編輯 header.html，在 </header> 調用系統內建模板 `google_analytics.html`
```
<header class="header">
        <div class="container header__container">
                {{ partial "logo.html" . }}
                {{ partial "menu.html" . }}
        </div>
{{ partial "google_analytics.html" . }} # 就是這裡
</header>
```

3. 回到 hugo 根目錄，修改 hugo.toml。加入 tracker ID
```
[services]
  [services.googleAnalytics]
    id = 'G-XXXXXX' # 這邊取代成你自己的 tracker ID
```

**[官網原文: Embedded partial templates. Hugo provides embedded partial templates for common use cases.](https://gohugo.io/templates/embedded/#configuration-google-analytics)**