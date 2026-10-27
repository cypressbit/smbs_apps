/*
 * Gallery lightbox: a photo in a gallery opens full screen, with previous and
 * next. Each photo is a link to its large copy, so without JavaScript it still
 * opens. Uses <dialog>: Escape closes it and focus returns to the photo.
 */
(function () {
  'use strict';

  let dialog, image, caption, count, links = [], index = 0, touchX = null;

  function button(className, label, icon, onClick) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = className;
    b.setAttribute('aria-label', label);
    b.innerHTML = `<i class="bi ${icon}" aria-hidden="true"></i>`;
    b.addEventListener('click', onClick);
    return b;
  }

  function build() {
    dialog = document.createElement('dialog');
    dialog.className = 'db-lightbox';
    dialog.setAttribute('aria-label', 'Photo viewer');
    const figure = document.createElement('figure');
    image = document.createElement('img');
    image.sizes = '100vw';
    caption = document.createElement('figcaption');
    count = document.createElement('div');
    count.className = 'db-lightbox-count';
    count.setAttribute('aria-live', 'polite');
    figure.append(image, caption);
    const close = button('db-lightbox-close', 'Close', 'bi-x-lg', () => dialog.close());
    close.autofocus = true;
    dialog.append(figure, count, close,
      button('db-lightbox-prev', 'Previous photo', 'bi-chevron-left', () => show(index - 1)),
      button('db-lightbox-next', 'Next photo', 'bi-chevron-right', () => show(index + 1)));
    // A click on the dark area around the photo closes it.
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') show(index - 1);
      if (event.key === 'ArrowRight') show(index + 1);
    });
    dialog.addEventListener('touchstart', (event) => { touchX = event.touches[0].clientX; }, {passive: true});
    dialog.addEventListener('touchend', (event) => {
      if (touchX === null) return;
      const moved = event.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(moved) > 50) show(index + (moved < 0 ? 1 : -1));
    });
    dialog.addEventListener('close', () => links[index] && links[index].focus());
    document.body.append(dialog);
  }

  function show(i) {
    index = (i + links.length) % links.length;
    const link = links[index];
    const thumb = link.querySelector('img');
    image.removeAttribute('srcset');
    if (thumb && thumb.srcset) image.srcset = thumb.srcset;
    image.src = link.href;
    image.alt = thumb ? thumb.alt : '';
    const text = link.closest('figure')?.querySelector('figcaption')?.textContent.trim() || '';
    caption.textContent = text;
    caption.hidden = !text;
    count.textContent = links.length > 1 ? `${index + 1} / ${links.length}` : '';
    dialog.querySelectorAll('.db-lightbox-prev, .db-lightbox-next').forEach((b) => { b.hidden = links.length < 2; });
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a.db-lightbox-link');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey || typeof HTMLDialogElement === 'undefined') return;
    event.preventDefault();
    if (!dialog) build();
    links = Array.from(link.closest('.db-gallery').querySelectorAll('a.db-lightbox-link'));
    show(links.indexOf(link));
    dialog.showModal();
  });
})();
