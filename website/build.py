import json, re, sys
from pathlib import Path
base=Path(__file__).resolve().parent
src=base.parent/'site'
p=(src/'template.html').read_text()
# Reuse the team's validated static snapshot and explorer. Escape script terminators in the embedded data.
page=(src/'index.html').read_text()
data=json.loads(page.split('const DATA = ',1)[1].split(';\n\nconst TASK_NAMES',1)[0])
model=next(iter(data['preliminary']), 'gemini-3.5-flash-lite')
v=data['preliminary'].get(model, {'en2kk':None,'kk2en':None,'gap':None,'pairs':0})
def score(x):return 'Pending' if x is None else f'{x:.2f}'
def direction(x):return 'Pending' if x is None else f'{x:+.2f}'.replace('-','−')
hero=f'''
<header><div class="wrap">
<a href="#" class="wordmark" aria-label="KAZLLM home"><span class="logomark">⇄</span>KAZLLM</a>
<nav class="jump" aria-label="Sections"><a href="#explorer">Explorer</a><a href="#scores">Results</a><a href="#method">Method</a></nav>
<a class="button small" href="#explorer">Open explorer <span aria-hidden="true">↗</span></a>
</div></header>
<section class="hero wrap" aria-labelledby="hero-title">
<div><span class="kicker">SE-2414 · Research demo</span>
<h1 id="hero-title">How well does AI<br><span>handle Kazakh?</span></h1>
<p>Explore a paired Kazakh–English benchmark. Read the original prompts, inspect saved model answers, and compare translation quality in both directions.</p>
<div class="hero-actions"><a class="button" href="#explorer">Explore the benchmark <span aria-hidden="true">→</span></a><a class="button secondary" href="#scores">View results</a></div></div>
<div class="orbit-stage" aria-label="Gemini translation comparison">
<div class="orbit-tag left"><span>Into Kazakh</span><b>{score(v["en2kk"])} chrF2</b></div>
<div class="ring"><div class="ring-core"><strong>{direction(v["gap"])}</strong><span>chrF2 gap</span></div></div>
<div class="orbit-tag right"><span>Into English</span><b>{score(v["kk2en"])} chrF2</b></div>
</div>
<p class="hero-note">{model} · {v["pairs"]} paired translations · Kazakh minus English</p>
</section>
<div class="fact-band"><div class="wrap">
<span><i>◇</i><b>{len(data["items"])}</b> benchmark items</span>
<span><i>⇄</i><b>{data["prompts_per_model"]}</b> prompts per model</span>
<span><i>◉</i><b>{sum(v['benchmark'] for v in data['counts'].values())}</b> saved benchmark responses</span>
</div></div>
'''
p=re.sub(r'<header>.*?</header>',lambda _:hero,p,count=1,flags=re.S)
p=p.replace('<title>KAZLLM Demo</title>','<title>KAZLLM · Kazakh–English Benchmark</title><meta name="description" content="Browse paired Kazakh–English benchmark items and real saved model responses.">')
p=re.sub(r'<link[^>]+(?:fonts.googleapis.com|fonts.gstatic.com)[^>]*>','',p)
p=p.replace('</style>','\n'+(base/'style.css').read_text()+'\n</style>\n</head><body>',1)
p=p.replace('<main>\n  <div class="wrap">','''<main>
  <div class="wrap">
    <section aria-labelledby="tasks-title">
      <div class="section-head"><h2 id="tasks-title">Three ways to <span class="accent">explore.</span></h2><p>Open a task to see the source, model answer, reference and scoring details.</p></div>
      <div class="modules">
      <a class="module" data-open-task="mt" href="#explorer"><span class="icon" aria-hidden="true">⇄</span><strong>Translation</strong><small>Inspect the same sentence in both directions.</small><span class="go">Explore translations →</span></a>
      <a class="module" data-open-task="qa" href="#explorer"><span class="icon" aria-hidden="true">?</span><strong>Question answering</strong><small>Compare model choices with the answer key.</small><span class="go">Explore questions →</span></a>
      <a class="module" data-open-task="probe" href="#explorer"><span class="icon" aria-hidden="true">◎</span><strong>Language probes</strong><small>See examples targeting Kazakh grammar.</small><span class="go">Explore probes →</span></a>
      </div>
    </section>''')
p=p.replace('200 FLORES-200 sentence pairs','200 translation pairs (140 FLORES-200 and 60 KazParC)')
p=p.replace('This is not the study result and will change as the run completes.','The scores cover the completed translation subset.')
p=p.replace('Any model has to beat these to show real ability. QA has four options, so chance is 25%.','Simple comparison rules evaluated on the full benchmark. Random QA has an expected accuracy of 25%.')
p=p.replace('Built from the saved records in <span class="mono">outputs/</span> and <span class="mono">smoke_outputs/</span> by <span class="mono">site/build_site.py</span>. The page makes no model calls.','<span>KAZLLM · SE-2414 · Research Methods and Tools</span><span>Saved responses · <a href="https://github.com/tw3tyy/kazllm">Project repository ↗</a></span>')
p=p.replace('if (items.length && !items.some(it => it.n === state.current)) select(items[0].n, false);','''if (items.length && !items.some(it => it.n === state.current)) select(items[0].n, true);
  else renderDetail();''')
p=p.replace('  const item = DATA.items[state.current - 1];\n  const chips', '''  const item = DATA.items[state.current - 1];
  if (!item || !matches(item)) {
    $("#detail").innerHTML = '<div class="pending-note">No items match these filters. Clear the search or change the model or task.</div>';
    return;
  }
  const chips''')
p=p.replace('  const sel = $("#model-select");','''  const sel = $("#model-select");
  document.querySelectorAll("[data-open-task]").forEach(link => link.addEventListener("click", () => {
    state.query = "";
    $("#search").value = "";
    state.answered = false;
    $("#answered").checked = false;
    document.querySelector(`.seg button[data-task="${link.dataset.openTask}"]`).click();
  }));''')
p=p.replace('if (b) select(+b.dataset.n);','if (b) { select(+b.dataset.n); if (matchMedia("(max-width: 760px)").matches) $("#detail").scrollIntoView({block:"start"}); }')
payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
p=p.replace('/*__KAZLLM_DATA__*/null',payload)
out=base/'index.html'
out.write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'+p+'\n</body></html>\n',encoding='utf-8')
print(out, len(data['items']),v)
