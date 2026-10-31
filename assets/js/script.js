const swiper = new Swiper('.swiper', {
  direction: 'horizontal',
  loop: false,
  lazyPreloadPrevNext: 1,

  pagination: {
    el: '.swiper-pagination',
    dynamicBullets: true,
  },

  navigation: {
    nextEl: '.swiper-button-next',
    prevEl: '.swiper-button-prev',
  },

  keyboard: {
    enabled: true,
    onlyInViewport: true,
    pageUpDown: false,
  },

  a11y: {
    prevSlideMessage: 'Попереднє фото',
    nextSlideMessage: 'Наступне фото',
    firstSlideMessage: 'Це перше фото',
    lastSlideMessage: 'Це останнє фото',
    slideLabelMessage: 'Фото {{index}} із {{slidesLength}}',
    containerRoleDescriptionMessage: 'галерея',
    itemRoleDescriptionMessage: 'фото',
  },
});