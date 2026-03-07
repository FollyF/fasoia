(function ($) {

  "use strict";

  // =========================
  // PRE LOADER
  // =========================
  $(window).on('load', function(){
      $('.preloader').fadeOut(1000); // 1 seconde pour disparaître
  });

  // =========================
  // MENU COLLAPSE AU CLIC
  // =========================
  $('.navbar-collapse a').on('click', function(){
      $(".navbar-collapse").collapse('hide');
  });

  // =========================
  // MENU FIXÉ AU SCROLL
  // =========================
  $(window).scroll(function() {
      if ($(".navbar").offset().top > 50) {
          $(".navbar-fixed-top").addClass("top-nav-collapse");
      } else {
          $(".navbar-fixed-top").removeClass("top-nav-collapse");
      }
  });

  // =========================
  // SLIDERS
  // =========================

  // Slider principal (Home)
  $('.home-slider').owlCarousel({
      animateOut: 'fadeOut',
      items: 1,
      loop: true,
      dots: false,
      autoplay: true,
      autoplayTimeout: 6000,      // 6 secondes par slide
      autoplayHoverPause: true,   // stop au survol pour lire le message
      smartSpeed: 800             // transition fluide
  });

  // Slider des cours
  $('.owl-courses').owlCarousel({
      animateOut: 'fadeOut',
      loop: true,
      autoplay: true,
      autoplayHoverPause: false,
      smartSpeed: 1000,
      dots: false,
      nav: true,
      navText: [
          '<i class="fa fa-angle-left"></i>',
          '<i class="fa fa-angle-right"></i>'
      ],
      responsiveClass: true,
      responsive: {
          0: { items: 1 },
          1000: { items: 3 }
      }
  });

  // Slider des clients
  $('.owl-client').owlCarousel({
      animateOut: 'fadeOut',
      loop: true,
      autoplay: true,
      autoplayHoverPause: false,
      smartSpeed: 1000,
      responsiveClass: true,
      responsive: {
          0: { items: 1 },
          1000: { items: 3 }
      }
  });

  // =========================
  // SMOOTH SCROLL POUR NAVIGATION
  // =========================
  $(function() {
      $('.custom-navbar a, #home a').on('click', function(event) {
          var $anchor = $(this);
          $('html, body').stop().animate({
              scrollTop: $($anchor.attr('href')).offset().top - 49
          }, 1000);
          event.preventDefault();
      });
  });

})(jQuery);
