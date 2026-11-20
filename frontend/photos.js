const cache = new Map();

function plainCredit(value) {
  const element = document.createElement("span");
  element.innerHTML = String(value || "");
  return (element.textContent || "").replace(/\s+/g, " ").trim().slice(0, 220);
}

async function findPhoto(id) {
  if (!cache.has(id)) {
    cache.set(id, fetch("/api/photos/" + encodeURIComponent(id))
      .then(async response => response.ok ? response.json() : null)
      .catch(() => null)
      .then(photo => {
        if (!photo) cache.delete(id);
        return photo;
      }));
  }
  return cache.get(id);
}

const observer = new IntersectionObserver(entries => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      observer.unobserve(entry.target);
      showPhoto(entry.target);
    }
  }
}, { rootMargin: "240px" });

async function showPhoto(target) {
  const photo = await findPhoto(target.dataset.photo);
  if (!target.isConnected) return;
  const placeholder = target.querySelector(".photo-placeholder");
  const unavailable = () => {
    target.dataset.photoState = "error";
    placeholder.textContent = `Фото ${target.dataset.alt} недоступно`;
  };
  if (!photo) return unavailable();
  const image = new Image();
  image.alt = target.dataset.alt;
  image.decoding = "async";
  image.referrerPolicy = "no-referrer";
  let tryingOriginal = false;
  image.addEventListener("error", () => {
    if (!target.isConnected) return;
    if (!tryingOriginal && photo.originalUrl) {
      tryingOriginal = true;
      image.src = photo.originalUrl;
    } else {
      unavailable();
    }
  });
  image.addEventListener("load", () => {
    if (!target.isConnected) return;
    placeholder.replaceWith(image);
    if (Array.isArray(photo.photos) && photo.photos.length > 1) {
      const gallery = document.createElement("div");
      gallery.className = "photo-gallery";
      for (const item of photo.photos) {
        const thumb = document.createElement("button");
        thumb.type = "button";
        thumb.className = "photo-thumb";
        thumb.title = "Показать фотографию";
        const thumbImage = document.createElement("img");
        thumbImage.src = item.url;
        thumbImage.alt = target.dataset.alt;
        thumb.append(thumbImage);
        thumb.addEventListener("click", () => { image.src = item.url; });
        gallery.append(thumb);
      }
      target.append(gallery);
    }
    const link = target.querySelector(".photo-credit");
    if (link) {
      link.href = photo.source;
      link.textContent = plainCredit(photo.credit) || "Источник и лицензия";
      link.hidden = false;
    }
    target.dataset.photoState = "loaded";
  }, { once: true });
  image.src = photo.url;

  // Keep additional openly licensed results available to the next UI update.
  // The first image remains the card cover; the API exposes up to three.
  target.dataset.photoCount = String(photo.photos?.length || 1);
}

export function observePhotos(root) {
  root.querySelectorAll("[data-photo]").forEach(element => observer.observe(element));
}
