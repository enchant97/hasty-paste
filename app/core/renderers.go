package core

import (
	"io"

	"github.com/alecthomas/chroma/v2"
	"github.com/alecthomas/chroma/v2/formatters/html"
	"github.com/alecthomas/chroma/v2/lexers"
	"github.com/alecthomas/chroma/v2/styles"
	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/extension"
	gm_html "github.com/yuin/goldmark/renderer/html"
)

func RenderSourceCode(lexerAlias string, content string, w io.Writer) error {
	lexer := chroma.Coalesce(lexers.Get(lexerAlias))
	style := styles.Get("github-dark")
	formatter := html.New(html.InlineCode(true))
	tokens, err := lexer.Tokenise(nil, content)
	if err != nil {
		return err
	}
	return formatter.Format(w, style, tokens)
}

func RenderMarkdown(content []byte, w io.Writer) error {
	md := goldmark.New(
		goldmark.WithExtensions(extension.GFM),
		goldmark.WithParserOptions(),
		goldmark.WithRendererOptions(
			gm_html.WithHardWraps(),
		),
	)
	return md.Convert(content, w)
}
