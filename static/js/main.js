// mobile nav
document.addEventListener("DOMContentLoaded", function () {
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  burger && burger.addEventListener('click', ()=> nav.classList.toggle('open'));
  nav && nav.querySelectorAll('a').forEach(a=>a.addEventListener('click', ()=>nav.classList.remove('open')));

  // scroll reveal
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
  },{threshold:.15});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

  // price tabs
  document.querySelectorAll('.price-tab').forEach(tab=>{
    tab.addEventListener('click', ()=>{
      document.querySelectorAll('.price-tab').forEach(t=>t.classList.remove('active'));
      document.querySelectorAll('.price-panel').forEach(p=>p.classList.remove('active'));
      tab.classList.add('active');
      document.querySelector(`.price-panel[data-panel="${tab.dataset.tab}"]`).classList.add('active');
    });
  });

  // faq accordion
  document.querySelectorAll('.faq-q').forEach(q=>{
    q.addEventListener('click', ()=>{
      const item = q.closest('.faq-item');
      const wasOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item').forEach(i=>i.classList.remove('open'));
      if(!wasOpen) item.classList.add('open');
    });
  });

  // before/after compare slider
  document.querySelectorAll('[data-compare]').forEach(box=>{
    const clip = box.querySelector('.compare-clip');
    const inner = clip.querySelector('.layer');
    let dragging = false;
    function setPos(clientX){
      const rect = box.getBoundingClientRect();
      let pct = ((clientX - rect.left) / rect.width) * 100;
      pct = Math.max(4, Math.min(96, pct));
      clip.style.width = pct + '%';
      inner.style.width = rect.width + 'px';
      box.querySelector('.compare-handle').style.left = pct + '%';
    }
    box.addEventListener('mousedown', e=>{ dragging = true; setPos(e.clientX); });
    window.addEventListener('mousemove', e=>{ if(dragging) setPos(e.clientX); });
    window.addEventListener('mouseup', ()=> dragging = false);
    box.addEventListener('touchstart', e=>{ dragging = true; setPos(e.touches[0].clientX); });
    box.addEventListener('touchmove', e=>{ if(dragging) setPos(e.touches[0].clientX); });
    box.addEventListener('touchend', ()=> dragging = false);
  });
});
