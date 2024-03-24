# Function: text_file and title are essential.
# generate_html(text_file, title, subtitle=None, time=None, header_image=None, short_intro=None, keywords=None)
#
# Example usage: python ../../tools/postBlog.py text_file.txt "Pico de Gallo,home recipes" "I thought I made too much, but it consumed faster than expected." "2023-06-04" "picodegallo.webp" "I have an immense fondness for pico de gallo. Its tantalizing flavors make my mouth water. However, I often find myself dissatisfied with the portion served in stores. Determined to satisfy my cravings, I took matters into my own hands, making a generous amount while customizing the seasoning to perfectly suit my taste buds." "Will, blog, pico de gallo, salsa, tortilla, mexican food, home recipes"

import sys

def generate_html(text_file, title, subtitle=None, time=None, header_image=None, short_intro=None, keywords=None):
    with open(text_file, 'r') as file:
        main_content = file.read()

    html_template = f"""<!DOCTYPE html>
<html lang="en-US">
	<head>
		<!-- Google tag (gtag.js) -->
		<script async src="https://www.googletagmanager.com/gtag/js?id=G-6XELVJJ51M"></script>
		<script>
		  window.dataLayer = window.dataLayer || [];
		  function gtag(){{dataLayer.push(arguments);}}
		  gtag('js', new Date());

		  gtag('config', 'G-6XELVJJ51M');
		</script>

		<meta charset="utf-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<link rel="stylesheet" href="../../style.css"/>

		<title>{title}{f'{subtitle}' if subtitle else ''}</title>
	    <meta property="og:title" content="{title}{f'{subtitle}' if subtitle else ''}">
	    <meta property="twitter:title" content="{title}{f'{subtitle}' if subtitle else ''}">	 

		<meta name="description" content="{f'{short_intro}' if short_intro else ''}" />    
		<meta property="og:description" content="{f'{short_intro}' if short_intro else ''}">
	    <meta property="twitter:description" content="{f'{short_intro}' if short_intro else ''}">

	    <meta name='keywords' content='{f'{keywords}' if keywords else ''}'>
	    <meta property="og:url" content="https://willscyber.net/blog/{title.replace(" ", "_")}.html">
	    <meta property="og:image" content="https://willscyber.net/blog/{f'{header_image}' if header_image else ''}">
        <meta property="twitter:image" content="https://willscyber.net/blog/{f'{header_image}' if header_image else ''}">

        <meta property="og:site_name" content="WILL's CYBER WAREHOUSE">  
        <meta property="twitter:card" content="summary_large_image">
	    <link rel="shortcut icon" href="/favicon.ico">

	    <style>
			p {{
			  line-height:150%;
			}}
		</style>

		<!--
	    	favicon resource: <a href="https://www.flaticon.com/free-icons/data-warehouse" title="data warehouse icons">Data warehouse icons created by Zulfa Mahendra - Flaticon</a>
	    -->
<!--color panel 
EVA organge rgb(230,119,11)
EVA purple rgb(118,88,152)
EVA green rgb(82,208,83)
EVA red  rgb(211,41,15)
EVA blue rgb(160,175,229)
-->
	</head>
	<body>
		<header id="site_header">
			<h1>
				<i>WILL's CYBER <sub>BLOG</sub></i>
			</h1>
			<nav>
		        <span><a href="/">home</a></span>
		        <span><a href="../blog.html" class="active">blog</a></span>
			</nav>
		</header>
		<div id="content">     
			<article class="article_header">
				<header style="text-align:center;">
					{f"<img src='{header_image}' alt='Header Image' style='padding-bottom: 10px;' layout='responsive' width='256px' height='192px'><br>" if header_image else ""}
					<div class="byline">
		                {f"<time datetime='{time}'>{time}</time>" if time else ""}
		                <span>by <span class="author by" id="author">Will</span></span>
		            </div>

		            <h1>{title}</h1>
		            {f"<strong id='lead'>{subtitle}</strong><br>" if subtitle else ""}
		            <hr>
				</header>
				<p>{f"{short_intro}" if short_intro else ""}</p>
				<p>{main_content}</p>
			</article>
		</div>
	</body>
	<footer style="text-align: center;">
	    <div style="justify-content: center">
	        <a href="https://twitter.com/william_y_chen" target="_blank"><img class="SNS" src="https://abs.twimg.com/responsive-web/client-web/icon-ios.b1fc727a.png" alt="twitter icon" title="twitter" width="40px" height="40px"></a>
	        <a rel="alternative" type="application/rss+xml" href="/blog/willscyber_blog_feed.xml"><img class="RSS" src="https://upload.wikimedia.org/wikipedia/en/4/43/Feed-icon.svg" alt="RSS icon" title="RSS" width="40px" height="40px"></a>
	    </div>
	</footer>
</html>
"""

    return html_template

def write_html(html_content):
    with open(f"{title.replace(' ', '_')}.html", "w") as f:
        f.write(html_content)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py text_file title [subtitle] [time] [header_image] [short_intro] [keywords]")
        sys.exit(1)

    text_file = sys.argv[1]
    title = sys.argv[2]
    subtitle = sys.argv[3] if len(sys.argv) > 3 else None
    time = sys.argv[4] if len(sys.argv) > 4 else None
    header_image = sys.argv[5] if len(sys.argv) > 5 else None
    short_intro = sys.argv[6] if len(sys.argv) > 6 else None
    keywords = sys.argv[7] if len(sys.argv) > 7 else None

    html_content = generate_html(text_file, title, subtitle, time, header_image, short_intro, keywords)
    write_html(html_content)
    print(f"HTML content generated and saved as {title.replace(' ', '_')}.html")