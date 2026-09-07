import { useEffect, useState } from "react";

/**
 * A markdown note, rendered.
 *
 * `marked` is a lazy `import()` inside the effect rather than a module-level import: notes
 * are one tab of one reader, and a visitor who never opens them should not download a
 * markdown parser to draw a plan.
 *
 * Raw HTML in the source is dropped rather than passed through. These notes are house-authored
 * prose and the local editor's copy is the user's own — but the same bundle serves them to
 * anyone on the published site, so the renderer has exactly one HTML author, which is `marked`
 * itself. That is what makes `dangerouslySetInnerHTML` here honest rather than a hazard.
 */
export function MarkdownBody({ markdown, titledAs }: {
  markdown: string;
  /** The heading the surrounding chrome already prints. A leading `# ` line matching it is
   *  dropped, so a note whose first line restates its own title does not say it twice. */
  titledAs?: string;
}) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    void (async () => {
      const { Marked } = await import("marked");
      // Our own instance, not the module singleton: a renderer override is global state on
      // the singleton, and a second consumer added later would silently inherit it.
      const marked = new Marked({ gfm: true, breaks: false });
      marked.use({
        renderer: {
          html: () => "",
          // An `<img src=x onerror=…>` written as markdown is still an author-supplied
          // attribute set, so images are dropped too — a note is prose, and none of the
          // house's carry one.
          image: () => "",
        },
      });
      const rendered = await marked.parse(stripLeadingTitle(markdown, titledAs));
      if (live) setHtml(rendered);
    })().catch(() => { if (live) setHtml(null); });
    return () => { live = false; };
  }, [markdown, titledAs]);

  // While the parser arrives, show the source. A note is readable as plain text — which is
  // the whole argument for keeping these in markdown — so there is nothing to spin for.
  if (html === null) {
    return <pre className="md-body" style={{ whiteSpace: "pre-wrap" }}>{markdown}</pre>;
  }
  return <div className="md-body" dangerouslySetInnerHTML={{ __html: html }} />;
}

/** Drop the note's own opening `# Title` when the chrome above it already says that. Only a
 *  leading heading, and only an exact match: a note whose first heading says something else
 *  is saying something else. */
function stripLeadingTitle(markdown: string, title?: string): string {
  if (!title) return markdown;
  const lines = markdown.split("\n");
  let at = 0;
  // Step over frontmatter, which the engine's note_title reads and this renderer should not
  // print as a table of stray text.
  if (lines[0]?.trim() === "---") {
    const end = lines.findIndex((line, index) => index > 0 && line.trim() === "---");
    if (end > 0) at = end + 1;
  }
  const body = lines.slice(at);
  const first = body.findIndex((line) => line.trim().length > 0);
  if (first >= 0 && body[first].startsWith("# ")
      && body[first].slice(2).trim() === title.trim()) {
    body.splice(first, 1);
  }
  return body.join("\n");
}
