export type Lang = 'ru' | 'en';
export const LANGS: Lang[] = ['ru', 'en'];

/** Address of a page in a language: localized('/wibes.html', 'en') → '/en/wibes.html' */
export function localized(path: string, lang: Lang): string {
  const clean = path.replace(/^\/en(\/|$)/, '/');
  return lang === 'en' ? `/en${clean === '/' ? '/' : clean}` : clean;
}

/** The language of an address */
export function langOf(path: string): Lang {
  return /^\/en(\/|$)/.test(path) ? 'en' : 'ru';
}

export const ui = {
  ru: {
    htmlLang: 'ru',
    ogLocale: 'ru_RU',
    siteName: 'Никитá Новá',
    siteTitle: 'Никитá Новá',
    tagline: 'дизайнер.',
    suffix: ' — Никита Нова',
    nav: { portfolio: 'Проекты', articles: 'Заметки', about: 'Обо мне', contact: 'Написать' },
    menu: { label: 'Меню', open: 'Открыть меню', close: 'Закрыть меню' },
    langSwitch: 'Выбор языка',
    footer: {
      copy: 'Никита Нова 2002 → 2026',
      label: 'Навигация в подвале',
      youtube: 'Ютуб',
      telegram: 'Тг канал',
      contact: 'Написать',
    },
    image: 'изображение',
    portfolioTitle: 'Портфолио',
    portfolioIntro: 'За 7 лет работы я сделала ',
    notesTitle: 'Заметки про дизайн',
    videoTitle: 'Видео',
    travelsTitle: 'Путешествия',
    meetupsTitle: 'Дизайн-воскресенье',
    meetupsIntro:
      '— это оффлайн-мероприятие, на котором мы гуляем → смотрим на дизайн реального мира → вместе делаем лучше',
    aboutTitle: 'Обо мне',
    consultationTitle: 'Консультации',
    notFoundTitle: 'Страница не найдена',
    signature: 'Никита Нова, дизайнер.',
    defaultDescription:
      'Меня правда зовут Никита. Я дизайнер с опытом менеджера, редактора, программиста, сценариста и арт‑директора',
  },
  en: {
    htmlLang: 'en',
    ogLocale: 'en_US',
    siteName: 'Nikita Nova',
    siteTitle: 'Nikita Nova',
    tagline: 'designer.',
    suffix: ' — Nikita Nova',
    nav: { portfolio: 'Portfolio', articles: 'Notes', about: 'About', contact: 'Contact' },
    menu: { label: 'Menu', open: 'Open menu', close: 'Close menu' },
    langSwitch: 'Language switch',
    footer: {
      copy: 'Nikita Nova 2002 → 2026',
      label: 'Footer navigation',
      youtube: 'YouTube',
      telegram: 'Telegram channel',
      contact: 'Contact',
    },
    image: 'image',
    portfolioTitle: 'Portfolio',
    portfolioIntro: 'In 7 years of work I made ',
    notesTitle: 'Notes about design',
    videoTitle: 'Video',
    travelsTitle: 'Travel',
    meetupsTitle: 'Design Sunday',
    meetupsIntro:
      '— an offline event where we walk around → look at the design of the real world → make it better together',
    aboutTitle: 'About me',
    consultationTitle: 'Consultations',
    notFoundTitle: 'Page not found',
    signature: 'Nikita Nova, designer.',
    defaultDescription:
      'My real name is Nikita. I am a designer with experience as a manager, editor, programmer, screenwriter and art director',
  },
} as const;

/** How the portfolio heading names each tag: «8 сайтов» / «8 websites» */
export const TAG_FORMS: Record<Lang, Record<string, readonly string[]>> = {
  ru: {
    'сайт': ['сайт', 'сайта', 'сайтов'],
    'промо-кампания': ['промо-кампания', 'промо-кампании', 'промо-кампаний'],
    'дроп одежды': ['дроп одежды', 'дропа одежды', 'дропов одежды'],
    'промышленный дизайн': ['проект в промышленном дизайне', 'проекта в промышленном дизайне', 'проектов в промышленном дизайне'],
    'графика': ['графика', 'графики', 'графики'],
    'упаковка': ['упаковка', 'упаковки', 'упаковок'],
    'навигация': ['навигация', 'навигации', 'навигаций'],
    'брендинг': ['брендинг', 'брендинга', 'брендингов'],
    'леттеринг': ['леттеринг', 'леттеринга', 'леттерингов'],
    'иллюстрация': ['иллюстрация', 'иллюстрации', 'иллюстраций'],
    'книга': ['книга', 'книги', 'книг'],
    'приложение': ['приложение', 'приложения', 'приложений'],
  },
  en: {
    'сайт': ['website', 'websites'],
    'промо-кампания': ['promo campaign', 'promo campaigns'],
    'дроп одежды': ['clothing drop', 'clothing drops'],
    'промышленный дизайн': ['industrial design project', 'industrial design projects'],
    'графика': ['graphics project', 'graphics projects'],
    'упаковка': ['packaging project', 'packaging projects'],
    'навигация': ['navigation project', 'navigation projects'],
    'брендинг': ['branding project', 'branding projects'],
    'леттеринг': ['lettering project', 'lettering projects'],
    'иллюстрация': ['illustration', 'illustrations'],
    'книга': ['book', 'books'],
    'приложение': ['app', 'apps'],
  },
};

/** «8 сайтов», «1 website» */
export function tagLabel(lang: Lang, tag: string, count: number): string {
  const forms = TAG_FORMS[lang][tag] ?? [tag];
  let form: string;
  if (lang === 'en') {
    form = forms[count === 1 ? 0 : 1] ?? forms[0];
  } else {
    const mod10 = count % 10;
    const mod100 = count % 100;
    const index = mod10 === 1 && mod100 !== 11 ? 0 : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14) ? 1 : 2;
    form = forms[index] ?? forms[0];
  }
  return `${count} ${form}`;
}
