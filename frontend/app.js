/**
 * Wave Music — Telegram Mini App Client Engine
 * Full audio playback, "Моя Волна", search, charts, and Telegram bot integration
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Telegram WebApp SDK
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    if (tg.setHeaderColor) tg.setHeaderColor('#0b0b10');
    if (tg.setBackgroundColor) tg.setBackgroundColor('#0b0b10');
  }

  function triggerHaptic(type = 'light') {
    try {
      tg?.HapticFeedback?.impactOccurred(type);
    } catch (e) {}
  }

  // 2. State & Collections
  const state = {
    currentTrack: null,
    isPlaying: false,
    queue: [],
    queueIndex: -1,
    currentMood: 'all',
    activeTab: 'tab-wave',
    isShuffle: false,
    isRepeat: false,
    favorites: JSON.parse(localStorage.getItem('wave_favorites') || '[]'),
    recent: JSON.parse(localStorage.getItem('wave_recent') || '[]')
  };

  // Full 100+ Track Catalog (Top Russian & World Hits)
  const defaultTracks = [
  {
    "id": "4EfM6rPmxow",
    "title": "Minor",
    "artist": "MiyaGi & Andy Panda",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "2:56",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "nidQCt_HEsY",
    "title": "I Got Love",
    "artist": "Miyagi & Эндшпиль feat. Рем Дигга",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "4:35",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "drive"
    ]
  },
  {
    "id": "j5cNhjG6iGs",
    "title": "Останься образом",
    "artist": "MACAN",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "3:12",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "romantic"
    ]
  },
  {
    "id": "7LcZzCPCuvg",
    "title": "По барам",
    "artist": "ANNA ASTI",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "3:58",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "p39HcuQNlg4",
    "title": "Прятки",
    "artist": "HammAli & Navai",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "3:10",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "x1XuN5Rq2ws",
    "title": "Ты и Я",
    "artist": "Xcho",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "2:45",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "yM1QjdoLmxQ",
    "title": "Комета",
    "artist": "JONY",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "2:38",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "energy"
    ]
  },
  {
    "id": "UJ3COIHd954",
    "title": "Captain",
    "artist": "Miyagi",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "3:40",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "drive"
    ]
  },
  {
    "id": "macan_asphalt8",
    "title": "Asphalt 8",
    "artist": "MACAN",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "3:15",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "anna_asti_tsaritsa",
    "title": "Царица",
    "artist": "ANNA ASTI",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:35",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "xcho_vorony",
    "title": "Вороны",
    "artist": "Xcho",
    "cover": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=400",
    "duration": "3:02",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "jony_besposhadna",
    "title": "Ты беспощадна",
    "artist": "JONY",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "3:44",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "hammali_ptichka",
    "title": "Птичка",
    "artist": "HammAli & Navai",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "3:05",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "drive"
    ]
  },
  {
    "id": "jah_khalib_medina",
    "title": "Медина",
    "artist": "Jah Khalib",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "3:48",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "dance"
    ]
  },
  {
    "id": "jah_khalib_leila",
    "title": "Лейла",
    "artist": "Jah Khalib",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "4:02",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "basta_sansara",
    "title": "Сансара",
    "artist": "Баста",
    "cover": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",
    "duration": "4:15",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "basta_medlyachok",
    "title": "Выпускной (Медлячок)",
    "artist": "Баста",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "5:35",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "scriptonite_polozhenie",
    "title": "Положение",
    "artist": "Скриптонит",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "4:12",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "scriptonite_eto_lubov",
    "title": "Это любовь",
    "artist": "Скриптонит",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "4:20",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "markul_strely",
    "title": "Стрелы",
    "artist": "Markul & Тося Чайкина",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "3:08",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "big_baby_tape_million",
    "title": "Million",
    "artist": "Big Baby Tape & Kizaru",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "2:30",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "big_baby_tape_99_problems",
    "title": "99 Problems",
    "artist": "Big Baby Tape & Kizaru",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "2:40",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "kizaru_dejavu",
    "title": "Дежавю",
    "artist": "Kizaru",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "3:02",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "oxxxymiron_gde_nas_net",
    "title": "Где нас нет",
    "artist": "Oxxxymiron",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "4:24",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "oxxxymiron_gorod_pod_podoshvoy",
    "title": "Город под подошвой",
    "artist": "Oxxxymiron",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "4:05",
    "category": "chart",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "feduk_moryak",
    "title": "Моряк",
    "artist": "Feduk",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "3:04",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "feduk_rozovoe_vino",
    "title": "Розовое вино",
    "artist": "Элджей & Feduk",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "4:06",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "ramil_siyay",
    "title": "Сияй",
    "artist": "Ramil'",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "3:18",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "romantic"
    ]
  },
  {
    "id": "navai_esenin",
    "title": "Есенин",
    "artist": "Navai",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "3:10",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "andro_inoplanetyanin",
    "title": "Инопланетянин",
    "artist": "Andro",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "3:24",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "the_limba_xo",
    "title": "X.O",
    "artist": "The Limba & Andro",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "3:01",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "morgenshtern_cristal_moet",
    "title": "Cristal & МОЁТ",
    "artist": "MORGENSHTERN",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "2:45",
    "category": "chart",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "morgenshtern_cadillac",
    "title": "Cadillac",
    "artist": "MORGENSHTERN & Элджей",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "2:57",
    "category": "chart",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "macan_za_vseh",
    "title": "За всех",
    "artist": "MACAN",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "3:10",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "miyagi_silhouette",
    "title": "Silhouette",
    "artist": "MiyaGi & Andy Panda",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "3:25",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "drive"
    ]
  },
  {
    "id": "miyagi_utopia",
    "title": "Utopia",
    "artist": "MiyaGi & Andy Panda",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "3:40",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "drive"
    ]
  },
  {
    "id": "xcho_eskizy",
    "title": "Эскизы",
    "artist": "Xcho",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "2:50",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "anna_asti_nochyu_na_kuhne",
    "title": "Ночью на кухне",
    "artist": "ANNA ASTI",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:50",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "pharaoh_diko_naprimer",
    "title": "Дико, например",
    "artist": "PHARAOH",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "2:40",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "rakhim_fendi",
    "title": "Fendi",
    "artist": "Rakhim",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "2:35",
    "category": "chart",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "fHI8X4OXluQ",
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "3:20",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "energy",
      "drive"
    ]
  },
  {
    "id": "Rif-RTvmmss",
    "title": "Starboy",
    "artist": "The Weeknd ft. Daft Punk",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:50",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "dance"
    ]
  },
  {
    "id": "the_weeknd_save_your_tears",
    "title": "Save Your Tears",
    "artist": "The Weeknd",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "3:35",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "romantic"
    ]
  },
  {
    "id": "the_weeknd_the_hills",
    "title": "The Hills",
    "artist": "The Weeknd",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "4:02",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "wjj2upnfBI0",
    "title": "Lovely",
    "artist": "Billie Eilish & Khalid",
    "cover": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",
    "duration": "3:20",
    "category": "world",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "billie_eilish_bad_guy",
    "title": "Bad Guy",
    "artist": "Billie Eilish",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "3:14",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "tR1ECf4sEpw",
    "title": "Lose Yourself",
    "artist": "Eminem",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "5:26",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "eminem_without_me",
    "title": "Without Me",
    "artist": "Eminem",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "4:50",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "drake_gods_plan",
    "title": "God's Plan",
    "artist": "Drake",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "3:19",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "drake_one_dance",
    "title": "One Dance",
    "artist": "Drake feat. Wizkid & Kyla",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "2:54",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "travis_scott_goosebumps",
    "title": "Goosebumps",
    "artist": "Travis Scott feat. Kendrick Lamar",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "4:03",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "travis_scott_sicko_mode",
    "title": "SICKO MODE",
    "artist": "Travis Scott feat. Drake",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "5:12",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "imagine_dragons_believer",
    "title": "Believer",
    "artist": "Imagine Dragons",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "3:24",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "imagine_dragons_radioactive",
    "title": "Radioactive",
    "artist": "Imagine Dragons",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:07",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "imagine_dragons_bones",
    "title": "Bones",
    "artist": "Imagine Dragons",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "2:45",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "dua_lipa_levitating",
    "title": "Levitating",
    "artist": "Dua Lipa",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "3:23",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "dua_lipa_dont_start_now",
    "title": "Don't Start Now",
    "artist": "Dua Lipa",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "3:03",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "arctic_monkeys_do_i_wanna_know",
    "title": "Do I Wanna Know?",
    "artist": "Arctic Monkeys",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "4:32",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "post_malone_circles",
    "title": "Circles",
    "artist": "Post Malone",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "3:35",
    "category": "world",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "post_malone_sunflower",
    "title": "Sunflower",
    "artist": "Post Malone & Swae Lee",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "2:38",
    "category": "world",
    "moods": [
      "all",
      "chill",
      "dance"
    ]
  },
  {
    "id": "harry_styles_as_it_was",
    "title": "As It Was",
    "artist": "Harry Styles",
    "cover": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",
    "duration": "2:47",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "ed_sheeran_shape_of_you",
    "title": "Shape of You",
    "artist": "Ed Sheeran",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "3:53",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "romantic"
    ]
  },
  {
    "id": "linkin_park_in_the_end",
    "title": "In The End",
    "artist": "Linkin Park",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:36",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "linkin_park_numb",
    "title": "Numb",
    "artist": "Linkin Park",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "3:07",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "nirvana_smells_like_teen_spirit",
    "title": "Smells Like Teen Spirit",
    "artist": "Nirvana",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "5:01",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "queen_bohemian_rhapsody",
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "5:55",
    "category": "world",
    "moods": [
      "all",
      "chill",
      "energy"
    ]
  },
  {
    "id": "kordhell_murder_in_my_mind",
    "title": "Murder In My Mind",
    "artist": "Kordhell",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "2:25",
    "category": "drive",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "dvrst_close_eyes",
    "title": "Close Eyes",
    "artist": "DVRST",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "2:12",
    "category": "drive",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "hensonn_sahara",
    "title": "Sahara",
    "artist": "Hensonn",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "2:51",
    "category": "drive",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "ghostface_playa_why_not",
    "title": "Why Not",
    "artist": "Ghostface Playa",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "2:46",
    "category": "drive",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "sxmpra_cowbell_warrior",
    "title": "COWBELL WARRIOR!",
    "artist": "SXMPRA",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "1:55",
    "category": "drive",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "pharmacist_north_memphis",
    "title": "North Memphis",
    "artist": "Pharmacist",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "2:20",
    "category": "drive",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "tiesto_the_business",
    "title": "The Business",
    "artist": "Tiësto",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "2:44",
    "category": "dance",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "meduza_piece_of_your_heart",
    "title": "Piece Of Your Heart",
    "artist": "Meduza ft. Goodboys",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "2:33",
    "category": "dance",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "fisher_losing_it",
    "title": "Losing It",
    "artist": "Fisher",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "4:08",
    "category": "dance",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "david_guetta_im_good",
    "title": "I'm Good (Blue)",
    "artist": "David Guetta & Bebe Rexha",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "2:55",
    "category": "dance",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "daft_punk_get_lucky",
    "title": "Get Lucky",
    "artist": "Daft Punk ft. Pharrell Williams",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "4:08",
    "category": "dance",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "miyagi_polovina_moya",
    "title": "Половина моя",
    "artist": "MiyaGi & Эндшпиль",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "3:30",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "miyagi_kosandra",
    "title": "Косандра",
    "artist": "MiyaGi & Andy Panda",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "3:45",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "drive"
    ]
  },
  {
    "id": "miyagi_lubi_menya",
    "title": "Люби меня",
    "artist": "MiyaGi & Эндшпиль feat. Симптом",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "3:55",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "chill"
    ]
  },
  {
    "id": "macan_kino",
    "title": "Кино",
    "artist": "MACAN",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "2:50",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "macan_yug",
    "title": "Юг",
    "artist": "MACAN",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "3:18",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "macan_ivl",
    "title": "ИВЛ",
    "artist": "MACAN feat. Scirena",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "3:22",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "drive"
    ]
  },
  {
    "id": "xcho_only_you",
    "title": "Only You",
    "artist": "Xcho",
    "cover": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "duration": "2:35",
    "category": "chart",
    "moods": [
      "all",
      "romantic",
      "dance"
    ]
  },
  {
    "id": "xcho_gandagan",
    "title": "Гандаган",
    "artist": "Xcho",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "2:40",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "anna_asti_durak",
    "title": "Дурак",
    "artist": "ANNA ASTI",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:25",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "anna_asti_zatmila",
    "title": "Затмила",
    "artist": "ANNA ASTI",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "3:40",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "scriptonite_vecherinka",
    "title": "Вечеринка",
    "artist": "Скриптонит",
    "cover": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400",
    "duration": "4:40",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "scriptonite_multibrendovy",
    "title": "Мультибрендовый",
    "artist": "Скриптонит feat. 104, T-Fest, Niman",
    "cover": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    "duration": "4:15",
    "category": "chart",
    "moods": [
      "all",
      "drive",
      "energy"
    ]
  },
  {
    "id": "jah_khalib_docha",
    "title": "Доча",
    "artist": "Jah Khalib",
    "cover": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",
    "duration": "3:38",
    "category": "chart",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "markul_serpantin",
    "title": "Серпантин",
    "artist": "Markul",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "3:05",
    "category": "chart",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "the_weeknd_cant_feel_my_face",
    "title": "Can't Feel My Face",
    "artist": "The Weeknd",
    "cover": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "duration": "3:35",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "the_weeknd_i_feel_it_coming",
    "title": "I Feel It Coming",
    "artist": "The Weeknd ft. Daft Punk",
    "cover": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400",
    "duration": "4:29",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "drake_hotline_bling",
    "title": "Hotline Bling",
    "artist": "Drake",
    "cover": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
    "duration": "4:27",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "chill"
    ]
  },
  {
    "id": "drake_in_my_feelings",
    "title": "In My Feelings",
    "artist": "Drake",
    "cover": "https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400",
    "duration": "3:37",
    "category": "world",
    "moods": [
      "all",
      "dance",
      "energy"
    ]
  },
  {
    "id": "travis_scott_highest_in_the_room",
    "title": "HIGHEST IN THE ROOM",
    "artist": "Travis Scott",
    "cover": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
    "duration": "2:55",
    "category": "world",
    "moods": [
      "all",
      "drive",
      "chill"
    ]
  },
  {
    "id": "travis_scott_fein",
    "title": "FE!N",
    "artist": "Travis Scott feat. Playboi Carti",
    "cover": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400",
    "duration": "3:11",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  },
  {
    "id": "billie_eilish_ocean_eyes",
    "title": "Ocean Eyes",
    "artist": "Billie Eilish",
    "cover": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",
    "duration": "3:20",
    "category": "world",
    "moods": [
      "all",
      "chill",
      "romantic"
    ]
  },
  {
    "id": "imagine_dragons_demons",
    "title": "Demons",
    "artist": "Imagine Dragons",
    "cover": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
    "duration": "2:57",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "romantic"
    ]
  },
  {
    "id": "imagine_dragons_whatever_it_takes",
    "title": "Whatever It Takes",
    "artist": "Imagine Dragons",
    "cover": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400",
    "duration": "3:21",
    "category": "world",
    "moods": [
      "all",
      "energy",
      "drive"
    ]
  }
];

  // Pre-fill queue initially
  state.queue = [...defaultTracks];

  // 3. DOM Elements
  const audio = document.getElementById('audioPlayer');
  
  // Navigation
  const navItems = document.querySelectorAll('.bottom-nav .nav-item');
  const tabPages = document.querySelectorAll('.tab-page');

  // Wave Tab
  const waveHeroCard = document.querySelector('.wave-hero-card');
  const waveOrb = document.getElementById('waveOrb');
  const waveStartBtn = document.getElementById('waveStartBtn');
  const moodChips = document.querySelectorAll('.mood-chip');
  const quickHitsContainer = document.getElementById('quickHitsContainer');
  const playlistsContainer = document.getElementById('playlistsContainer');
  const viewAllHits = document.getElementById('viewAllHits');

  // Search Tab
  const searchInput = document.getElementById('searchInput');
  const clearSearchBtn = document.getElementById('clearSearchBtn');
  const searchLoader = document.getElementById('searchLoader');
  const searchResultsList = document.getElementById('searchResultsList');
  const searchTags = document.querySelectorAll('.search-tag');

  // Chart Tab
  const chartList = document.getElementById('chartList');
  const playChartBtn = document.getElementById('playChartBtn');

  // Library Tab
  const libraryList = document.getElementById('libraryList');
  const emptyLibraryNotice = document.getElementById('emptyLibraryNotice');
  const favCountBadge = document.getElementById('favCountBadge');
  const libTabs = document.querySelectorAll('.lib-tab');
  const goToWaveBtn = document.getElementById('goToWaveBtn');

  // Mini Player
  const miniPlayer = document.getElementById('miniPlayer');
  const miniProgressLine = document.getElementById('miniProgressLine');
  const miniPlayerOpenArea = document.getElementById('miniPlayerOpenArea');
  const miniCover = document.getElementById('miniCover');
  const miniTitle = document.getElementById('miniTitle');
  const miniArtist = document.getElementById('miniArtist');
  const miniPlayBtn = document.getElementById('miniPlayBtn');
  const miniPlayIcon = document.getElementById('miniPlayIcon');
  const miniLikeBtn = document.getElementById('miniLikeBtn');
  const miniNextBtn = document.getElementById('miniNextBtn');

  // Full Player Modal
  const fullPlayerModal = document.getElementById('fullPlayerModal');
  const modalBackdrop = document.getElementById('modalBackdrop');
  const closeFullPlayerBtn = document.getElementById('closeFullPlayerBtn');
  const fullCover = document.getElementById('fullCover');
  const fullTitle = document.getElementById('fullTitle');
  const fullArtist = document.getElementById('fullArtist');
  const fullLikeBtn = document.getElementById('fullLikeBtn');
  const progressBarWrapper = document.getElementById('progressBarWrapper');
  const progressFill = document.getElementById('progressFill');
  const progressHandle = document.getElementById('progressHandle');
  const currentTimeLabel = document.getElementById('currentTime');
  const totalDurationLabel = document.getElementById('totalDuration');
  const fullPlayBtn = document.getElementById('fullPlayBtn');
  const fullPlayIcon = document.getElementById('fullPlayIcon');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const shuffleBtn = document.getElementById('shuffleBtn');
  const repeatBtn = document.getElementById('repeatBtn');
  const sendToChatBtn = document.getElementById('sendToChatBtn');
  const downloadMp3Btn = document.getElementById('downloadMp3Btn');
  const coverHalo = document.getElementById('coverHalo');
  const toast = document.getElementById('toast');

  // Access Control Modal Elements
  const accessGateModal = document.getElementById('accessGateModal');
  const accessUserName = document.getElementById('accessUserName');
  const accessUserId = document.getElementById('accessUserId');
  const sendAccessRequestBtn = document.getElementById('sendAccessRequestBtn');
  const checkAccessStatusBtn = document.getElementById('checkAccessStatusBtn');
  const accessStatusNotice = document.getElementById('accessStatusNotice');

  // Access State
  const initialUserId = tg?.initDataUnsafe?.user?.id || (new URLSearchParams(window.location.search).get('user_id')) || 0;
  state.currentUserId = initialUserId ? parseInt(initialUserId, 10) : 0;
  state.isAccessAllowed = false;
  state.isAdmin = false;

  async function checkUserAccess() {
    const tgUser = tg?.initDataUnsafe?.user;
    let uid = state.currentUserId || tgUser?.id;
    if (!uid) {
      const urlUid = new URLSearchParams(window.location.search).get('user_id');
      if (urlUid) uid = parseInt(urlUid, 10);
    }
    state.currentUserId = uid || 0;

    if (!uid) {
      // If opened outside Telegram without user_id, check version or allow preview
      return;
    }

    try {
      const res = await fetch(`/api/check_access?user_id=${uid}`);
      if (res.ok) {
        const data = await res.json();
        state.isAccessAllowed = Boolean(data.allowed);
        state.isAdmin = Boolean(data.is_admin);

        if (!state.isAccessAllowed) {
          showAccessGate(tgUser || { id: uid, first_name: 'Пользователь' });
          if (audio) {
            audio.pause();
            state.isPlaying = false;
            updatePlayPauseState(false);
          }
        } else {
          hideAccessGate();
        }
      }
    } catch (e) {
      console.warn('Access check error:', e);
    }
  }

  function showAccessGate(user) {
    if (!accessGateModal) return;
    accessGateModal.style.display = 'flex';
    if (accessUserName) accessUserName.textContent = user.first_name || 'Пользователь';
    if (accessUserId) accessUserId.textContent = `ID: ${user.id || state.currentUserId}`;

    const requested = localStorage.getItem(`wave_access_requested_${user.id || state.currentUserId}`);
    if (requested) {
      if (sendAccessRequestBtn) {
        sendAccessRequestBtn.disabled = true;
        sendAccessRequestBtn.innerHTML = '<span>⏳ Запрос на рассмотрении</span>';
      }
      if (checkAccessStatusBtn) checkAccessStatusBtn.style.display = 'flex';
      if (accessStatusNotice) {
        accessStatusNotice.style.display = 'block';
        accessStatusNotice.textContent = 'Ваш запрос отправлен администратору. Когда он подтвердит заявку, нажмите «Проверить одобрение» ниже.';
      }
    }
  }

  function hideAccessGate() {
    if (accessGateModal) accessGateModal.style.display = 'none';
  }

  if (sendAccessRequestBtn) {
    sendAccessRequestBtn.addEventListener('click', async () => {
      triggerHaptic('medium');
      const tgUser = tg?.initDataUnsafe?.user;
      const uid = state.currentUserId || tgUser?.id;
      if (!uid) {
        showToast('Не удалось определить Telegram ID');
        return;
      }

      sendAccessRequestBtn.disabled = true;
      sendAccessRequestBtn.innerHTML = '<span>⏳ Отправка...</span>';

      try {
        const res = await fetch('/api/request_access', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: uid,
            first_name: tgUser?.first_name || 'Пользователь',
            username: tgUser?.username || ''
          })
        });

        const data = await res.json();
        if (data.success) {
          localStorage.setItem(`wave_access_requested_${uid}`, 'true');
          sendAccessRequestBtn.innerHTML = '<span>✅ Запрос отправлен!</span>';
          if (checkAccessStatusBtn) checkAccessStatusBtn.style.display = 'flex';
          if (accessStatusNotice) {
            accessStatusNotice.style.display = 'block';
            accessStatusNotice.textContent = 'Администратор получил ваш запрос. Как только доступ откроют, нажмите кнопку «Проверить одобрение».';
          }
          showToast('📩 Запрос отправлен администратору!');
        } else {
          sendAccessRequestBtn.disabled = false;
          sendAccessRequestBtn.innerHTML = '<span>📩 Отправить запрос админу</span>';
          showToast(data.error || 'Ошибка при отправке');
        }
      } catch (err) {
        sendAccessRequestBtn.disabled = false;
        sendAccessRequestBtn.innerHTML = '<span>📩 Отправить запрос админу</span>';
        showToast('Ошибка сети. Попробуйте еще раз.');
      }
    });
  }

  if (checkAccessStatusBtn) {
    checkAccessStatusBtn.addEventListener('click', async () => {
      triggerHaptic('light');
      checkAccessStatusBtn.innerHTML = '<span>⏳ Проверка...</span>';
      await checkUserAccess();
      checkAccessStatusBtn.innerHTML = '<span>🔄 Проверить одобрение</span>';
      if (state.isAccessAllowed) {
        showToast('🎉 Доступ одобрен! Добро пожаловать!');
      } else {
        showToast('⏳ Заявка еще на рассмотрении администратора');
      }
    });
  }

  // 4. Toast Helper
  function showToast(text, duration = 3000) {
    toast.textContent = text;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }

  // 5. Audio Engine Functions
  function loadAndPlay(track, source = 'Моя Волна') {
    if (state.currentUserId && !state.isAccessAllowed) {
      showAccessGate(tg?.initDataUnsafe?.user || { id: state.currentUserId });
      showToast('🔒 Требуется одобрение администратора', 3000);
      return;
    }
    state.currentTrack = track;
    document.getElementById('playerSourceLabel').textContent = source;

    // Save to recents
    const existingIndex = state.recent.findIndex(t => t.id === track.id || t.title === track.title);
    if (existingIndex !== -1) state.recent.splice(existingIndex, 1);
    state.recent.unshift(track);
    if (state.recent.length > 50) state.recent.pop();
    localStorage.setItem('wave_recent', JSON.stringify(state.recent));

    // Update UI elements
    updateTrackMetadataUI(track);

    // Stream URL resolution: prioritize valid YouTube ID or "Artist - Title"
    let streamId = track.id;
    if (!streamId || streamId.startsWith('track_')) {
      streamId = `${track.artist} ${track.title}`;
    }
    showToast(`▶ ${track.artist} — ${track.title}`, 2000);
    const userParam = state.currentUserId ? `&user_id=${state.currentUserId}` : '';
    const streamUrl = `/api/stream?id=${encodeURIComponent(streamId)}${userParam}`;
    if (!audio.src || !audio.src.includes(encodeURIComponent(streamId))) {
      audio.src = streamUrl;
    }
    const playPromise = audio.play();
    if (playPromise !== undefined) {
      playPromise.then(() => {
        state.isPlaying = true;
        updatePlayPauseState(true);
      }).catch(err => {
        console.warn('Playback error or waiting for user gesture:', err);
        state.isPlaying = false;
        updatePlayPauseState(false);
        showToast('Нажмите Play для воспроизведения', 2500);
      });
    }

    // Update MediaSession for lockscreen & background play
    if ('mediaSession' in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: track.title,
        artist: track.artist,
        artwork: [
          { src: track.cover, sizes: '512x512', type: 'image/jpeg' }
        ]
      });
      navigator.mediaSession.setActionHandler('play', () => togglePlay());
      navigator.mediaSession.setActionHandler('pause', () => togglePlay());
      navigator.mediaSession.setActionHandler('nexttrack', () => playNext());
      navigator.mediaSession.setActionHandler('previoustrack', () => playPrev());
    }

    // Show Mini Player if hidden
    miniPlayer.style.display = 'flex';
  }

  function togglePlay() {
    triggerHaptic();
    if (!state.currentTrack) {
      if (state.queue.length > 0) {
        state.queueIndex = 0;
        loadAndPlay(state.queue[0]);
      }
      return;
    }

    if (audio.paused) {
      audio.play().then(() => {
        state.isPlaying = true;
        updatePlayPauseState(true);
      }).catch(e => console.error(e));
    } else {
      audio.pause();
      state.isPlaying = false;
      updatePlayPauseState(false);
    }
  }

  function playNext() {
    triggerHaptic();
    if (state.queue.length === 0) return;
    
    if (state.isShuffle) {
      state.queueIndex = Math.floor(Math.random() * state.queue.length);
    } else {
      state.queueIndex = (state.queueIndex + 1) % state.queue.length;
    }
    loadAndPlay(state.queue[state.queueIndex]);

    // Infinite Моя Волна: auto-append more tracks when approaching queue end
    if (state.queueIndex >= state.queue.length - 3 && document.getElementById('playerSourceLabel')?.textContent?.includes('Волна')) {
      fetch(`/api/wave?mood=${state.currentMood}`).then(r => r.json()).then(data => {
        if (data.tracks && data.tracks.length > 0) {
          const currentIds = new Set(state.queue.map(t => t.id));
          const newOnes = data.tracks.filter(t => !currentIds.has(t.id));
          if (newOnes.length > 0) state.queue.push(...newOnes);
        }
      }).catch(() => {});
    }
  }

  function playPrev() {
    triggerHaptic();
    if (state.queue.length === 0) return;
    if (audio.currentTime > 3) {
      audio.currentTime = 0;
      return;
    }
    state.queueIndex = (state.queueIndex - 1 + state.queue.length) % state.queue.length;
    loadAndPlay(state.queue[state.queueIndex]);
  }

  function updatePlayPauseState(isPlaying) {
    const playIconSvg = '<path d="M8 5v14l11-7z"/>';
    const pauseIconSvg = '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>';

    if (isPlaying) {
      miniPlayIcon.innerHTML = pauseIconSvg;
      fullPlayIcon.innerHTML = pauseIconSvg;
      waveHeroCard.classList.add('playing');
    } else {
      miniPlayIcon.innerHTML = playIconSvg;
      fullPlayIcon.innerHTML = playIconSvg;
      waveHeroCard.classList.remove('playing');
    }
  }

  function updateTrackMetadataUI(track) {
    miniTitle.textContent = track.title;
    miniArtist.textContent = track.artist;
    miniCover.src = track.cover;

    fullTitle.textContent = track.title;
    fullArtist.textContent = track.artist;
    fullCover.src = track.cover;

    // Check liked status
    const isLiked = state.favorites.some(t => t.id === track.id || t.title === track.title);
    miniLikeBtn.classList.toggle('active', isLiked);
    fullLikeBtn.classList.toggle('active', isLiked);

    // Active track in lists
    document.querySelectorAll('.track-item').forEach(item => {
      const match = item.dataset.id === track.id || item.dataset.title === track.title;
      item.classList.toggle('playing', match);
    });
  }

  // Audio Event Listeners
  audio.addEventListener('timeupdate', () => {
    if (!audio.duration) return;
    const progress = (audio.currentTime / audio.duration) * 100;
    progressFill.style.width = `${progress}%`;
    progressHandle.style.left = `${progress}%`;
    miniProgressLine.style.width = `${progress}%`;

    currentTimeLabel.textContent = formatTime(audio.currentTime);
    totalDurationLabel.textContent = formatTime(audio.duration);
  });

  audio.addEventListener('ended', () => {
    if (state.isRepeat) {
      audio.currentTime = 0;
      audio.play();
    } else {
      playNext();
    }
  });

  audio.addEventListener('playing', () => {
    state.isPlaying = true;
    updatePlayPauseState(true);
  });

  audio.addEventListener('pause', () => {
    state.isPlaying = false;
    updatePlayPauseState(false);
  });

  audio.addEventListener('error', (e) => {
    const err = audio.error;
    if (!audio.src) return;
    console.warn('Audio stream error:', err);
    state.isPlaying = false;
    updatePlayPauseState(false);
    if (err && err.code === 1) {
      // Aborted by user action, do not show error
      return;
    }
    showToast('⚠️ Ошибка загрузки трека. Нажмите для повтора', 3000);
  });

  function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }

  // Scrubber click / drag
  progressBarWrapper.addEventListener('click', (e) => {
    if (!audio.duration) return;
    const rect = progressBarWrapper.getBoundingClientRect();
    const clickPos = (e.clientX - rect.left) / rect.width;
    audio.currentTime = clickPos * audio.duration;
  });

  // 6. Navigation Tabs
  navItems.forEach(btn => {
    btn.addEventListener('click', () => {
      triggerHaptic();
      const target = btn.dataset.target;
      navItems.forEach(b => b.classList.remove('active'));
      tabPages.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
      state.activeTab = target;

      if (target === 'tab-library') renderLibrary();
      if (target === 'tab-chart') renderChart();
    });
  });

  // 7. "Моя Волна" Interactions
  waveOrb.addEventListener('click', () => {
    if (!state.isPlaying && !state.currentTrack) {
      startWave();
    } else {
      togglePlay();
    }
  });

  waveStartBtn.addEventListener('click', () => {
    triggerHaptic('medium');
    startWave();
  });

  moodChips.forEach(chip => {
    chip.addEventListener('click', () => {
      triggerHaptic();
      moodChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.currentMood = chip.dataset.mood;
      showToast(`Настроение волны: ${chip.textContent.trim()}`);
      startWave(true);
    });
  });

  const searchHeaderShortcut = document.getElementById('searchHeaderShortcut');
  if (searchHeaderShortcut) {
    searchHeaderShortcut.addEventListener('click', () => {
      document.querySelector('.bottom-nav [data-target="tab-search"]').click();
    });
  }

  async function startWave(forceNext = false) {
    showToast('Моя Волна настраивается...');
    try {
      const res = await fetch(`/api/wave?mood=${state.currentMood}`);
      if (res.ok) {
        const data = await res.json();
        if (data.tracks && data.tracks.length > 0) {
          state.queue = data.tracks;
          state.queueIndex = 0;
          const moodNames = {
            'all': 'Все треки', 'energy': 'Энергия', 'chill': 'Спокойствие',
            'drive': 'В дорогу', 'dance': 'Ритм', 'romantic': 'Лирика'
          };
          loadAndPlay(state.queue[0], `Моя Волна • ${moodNames[state.currentMood] || 'Поток'}`);
          showToast(`🌊 В потоке ${data.tracks.length} треков!`);
          return;
        }
      }
    } catch (err) {
      console.warn('Backend wave endpoint offline, using local smart stream:', err);
    }

    const moodTracks = defaultTracks.filter(t => !t.moods || t.moods.includes(state.currentMood) || state.currentMood === 'all');
    state.queue = (moodTracks.length > 0 ? moodTracks : defaultTracks).sort(() => Math.random() - 0.5);
    state.queueIndex = 0;
    loadAndPlay(state.queue[0], 'Моя Волна');
    showToast(`🌊 В потоке ${state.queue.length} треков!`);
  }

  // 8. Search Functionality
  let searchTimeout = null;
  let activeSearchId = 0;

  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim();
    clearSearchBtn.style.display = q ? 'block' : 'none';
    clearTimeout(searchTimeout);
    if (!q) {
      searchResultsList.innerHTML = '';
      searchLoader.style.display = 'none';
      return;
    }
    searchLoader.style.display = 'flex';
    searchTimeout = setTimeout(() => executeSearch(q), 300);
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      clearTimeout(searchTimeout);
      const q = searchInput.value.trim();
      if (q) {
        searchLoader.style.display = 'flex';
        executeSearch(q);
        searchInput.blur();
      }
    }
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    searchResultsList.innerHTML = '';
    searchLoader.style.display = 'none';
  });

  searchTags.forEach(tag => {
    tag.addEventListener('click', () => {
      triggerHaptic();
      const q = tag.dataset.query;
      searchInput.value = q;
      clearSearchBtn.style.display = 'block';
      searchLoader.style.display = 'flex';
      executeSearch(q);
    });
  });

  async function executeSearch(query) {
    if (state.currentUserId && !state.isAccessAllowed) {
      showAccessGate(tg?.initDataUnsafe?.user || { id: state.currentUserId });
      showToast('🔒 Поиск доступен после одобрения администратором');
      searchLoader.style.display = 'none';
      return;
    }
    const currentId = ++activeSearchId;
    try {
      const userParam = state.currentUserId ? `&user_id=${state.currentUserId}` : '';
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}${userParam}`);
      if (currentId !== activeSearchId) return;
      if (res.ok) {
        const data = await res.json();
        searchLoader.style.display = 'none';
        const tracks = data.tracks || [];
        if (tracks.length > 0) {
          renderTrackList(tracks, searchResultsList, 'Поиск: ' + query);
        } else {
          searchResultsList.innerHTML = `
            <div class="empty-state">
              <p style="font-weight: 600; margin-bottom: 6px;">Ничего не найдено</p>
              <p style="color: var(--text-muted); font-size: 13px;">Проверьте правильность написания исполнителя или трека</p>
            </div>
          `;
        }
        return;
      }
    } catch (e) {
      console.warn('Search API error:', e);
    }

    if (currentId !== activeSearchId) return;
    searchLoader.style.display = 'none';

    // Local fallback if offline
    const localFiltered = defaultTracks.filter(t => 
      t.title.toLowerCase().includes(query.toLowerCase()) || 
      t.artist.toLowerCase().includes(query.toLowerCase())
    );
    renderTrackList(localFiltered, searchResultsList, 'Поиск: ' + query);
  }

  // 9. Render Lists
  function renderTrackList(tracks, container, sourceName = 'Плейлист', showRank = false) {
    container.innerHTML = '';
    if (tracks.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>Ничего не найдено</p></div>';
      return;
    }

    tracks.forEach((track, index) => {
      const item = document.createElement('div');
      item.className = 'track-item';
      item.dataset.id = track.id || track.title;
      item.dataset.title = track.title;
      if (state.currentTrack && (state.currentTrack.id === track.id || state.currentTrack.title === track.title)) {
        item.classList.add('playing');
      }

      const isLiked = state.favorites.some(t => t.id === track.id || t.title === track.title);

      item.innerHTML = `
        <div class="track-item-left">
          ${showRank ? `<span class="chart-rank-num ${index < 3 ? 'top-3' : ''}">${index + 1}</span>` : ''}
          <img class="track-item-cover" src="${track.cover}" alt="cover" loading="lazy">
          <div class="track-item-info">
            <div class="track-item-title">${escapeHtml(track.title)}</div>
            <div class="track-item-artist">${escapeHtml(track.artist)} • ${track.duration || '3:00'}</div>
          </div>
        </div>
        <div class="track-item-actions">
          <button class="track-item-action-btn like-btn ${isLiked ? 'active' : ''}" data-track-idx="${index}">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="${isLiked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
            </svg>
          </button>
        </div>
      `;

      // Click anywhere on row to play (excluding like button)
      item.addEventListener('click', (e) => {
        if (e.target.closest('.like-btn')) return;
        triggerHaptic();
        state.queue = [...tracks];
        state.queueIndex = index;
        loadAndPlay(track, sourceName);
      });

      // Like button click
      const likeBtn = item.querySelector('.like-btn');
      likeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        triggerHaptic();
        toggleFavorite(track);
        likeBtn.classList.toggle('active');
        const svg = likeBtn.querySelector('svg');
        svg.setAttribute('fill', likeBtn.classList.contains('active') ? 'currentColor' : 'none');
      });

      container.appendChild(item);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[m]);
  }

  // 10. Favorites & Library
  function toggleFavorite(track) {
    const idx = state.favorites.findIndex(t => t.id === track.id || t.title === track.title);
    if (idx !== -1) {
      state.favorites.splice(idx, 1);
      showToast('Удалено из любимого');
    } else {
      state.favorites.unshift(track);
      showToast('❤️ Добавлено в Любимое');
    }
    localStorage.setItem('wave_favorites', JSON.stringify(state.favorites));

    // Update player heart buttons if currently playing
    if (state.currentTrack && (state.currentTrack.id === track.id || state.currentTrack.title === track.title)) {
      const isLiked = idx === -1;
      miniLikeBtn.classList.toggle('active', isLiked);
      fullLikeBtn.classList.toggle('active', isLiked);
    }
    favCountBadge.textContent = `${state.favorites.length} треков`;
  }

  miniLikeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (state.currentTrack) toggleFavorite(state.currentTrack);
  });

  fullLikeBtn.addEventListener('click', () => {
    if (state.currentTrack) toggleFavorite(state.currentTrack);
  });

  let currentLibFilter = 'favorites';
  libTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      triggerHaptic();
      libTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentLibFilter = tab.dataset.filter;
      renderLibrary();
    });
  });

  function renderLibrary() {
    const list = currentLibFilter === 'favorites' ? state.favorites : state.recent;
    favCountBadge.textContent = `${list.length} треков`;
    if (list.length === 0) {
      libraryList.innerHTML = '';
      emptyLibraryNotice.style.display = 'block';
    } else {
      emptyLibraryNotice.style.display = 'none';
      renderTrackList(list, libraryList, currentLibFilter === 'favorites' ? 'Моя коллекция' : 'Недавние');
    }
  }

  goToWaveBtn.addEventListener('click', () => {
    document.querySelector('.bottom-nav [data-target="tab-wave"]').click();
  });

  // 11. Chart & Home Quick Content (Daily Dynamic Updating)
  let liveChartTracks = defaultTracks.slice(0, 50);
  let liveReleaseTracks = defaultTracks.slice(15, 55);

  async function fetchLiveDailyMusic() {
    try {
      const [resChart, resReleases] = await Promise.all([
        fetch('/api/chart').then(r => r.ok ? r.json() : null),
        fetch('/api/new_releases').then(r => r.ok ? r.json() : null)
      ]);

      if (resChart && resChart.tracks && resChart.tracks.length > 0) {
        liveChartTracks = resChart.tracks;
        renderChart();
      }

      if (resReleases && resReleases.tracks && resReleases.tracks.length > 0) {
        liveReleaseTracks = resReleases.tracks;
        renderHomeHits();
      }
    } catch (e) {
      console.warn('Could not fetch daily updates, using local curated:', e);
    }
  }

  function renderChart() {
    renderTrackList(liveChartTracks, chartList, 'Главный Чарт (Ежедневный ТОП)', true);
  }

  playChartBtn.addEventListener('click', () => {
    triggerHaptic('medium');
    state.queue = [...liveChartTracks];
    state.queueIndex = 0;
    loadAndPlay(state.queue[0], 'Главный Чарт');
  });

  function renderHomeHits() {
    quickHitsContainer.innerHTML = '';
    liveReleaseTracks.forEach((track, idx) => {
      const card = document.createElement('div');
      card.className = 'hit-card';
      card.innerHTML = `
        <img class="hit-card-cover" src="${track.cover}" alt="cover" loading="lazy">
        <div class="hit-card-title">${escapeHtml(track.title)}</div>
        <div class="hit-card-artist">${escapeHtml(track.artist)}</div>
      `;
      card.addEventListener('click', () => {
        triggerHaptic();
        state.queue = [...liveReleaseTracks];
        state.queueIndex = idx;
        loadAndPlay(track, 'Горячие новинки дня');
      });
      quickHitsContainer.appendChild(card);
    });

    viewAllHits.addEventListener('click', () => {
      document.querySelector('.bottom-nav [data-target="tab-chart"]').click();
    });

    // Playlists Grid (6 distinct rich collections)
    const playlists = [
      { name: 'Главный ТОП 100', count: '100 треков', img: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300' },
      { name: 'Кальянный Рэп', count: '50 треков', img: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300' },
      { name: 'Deep & Chill House', count: '40 треков', img: 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=300' },
      { name: 'Восточный Вайб', count: '35 треков', img: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300' },
      { name: 'Phonk & Драйв в авто', count: '30 треков', img: 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=300' },
      { name: 'Зарубежные Мегахиты', count: '40 треков', img: 'https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=300' }
    ];

    playlistsContainer.innerHTML = '';
    playlists.forEach(pl => {
      const pCard = document.createElement('div');
      pCard.className = 'playlist-card';
      pCard.innerHTML = `
        <img class="playlist-card-img" src="${pl.img}" alt="cover">
        <div class="playlist-card-info">
          <div class="playlist-card-name">${pl.name}</div>
          <div class="playlist-card-count">${pl.count}</div>
        </div>
      `;
      pCard.addEventListener('click', async () => {
        triggerHaptic();
        showToast(`Загрузка плейлиста: ${pl.name}...`);
        try {
          const res = await fetch(`/api/playlist?name=${encodeURIComponent(pl.name)}`);
          if (res.ok) {
            const data = await res.json();
            if (data.tracks && data.tracks.length > 0) {
              state.queue = data.tracks;
              state.queueIndex = 0;
              loadAndPlay(state.queue[0], pl.name);
              showToast(`Плейлист «${pl.name}» (${data.tracks.length} треков)`);
              return;
            }
          }
        } catch (e) {}

        // Fallback filtering from catalog
        let filtered = [];
        const low = pl.name.toLowerCase();
        if (low.includes('кальян') || low.includes('рэп')) {
          filtered = defaultTracks.filter(t => t.category === 'chart');
        } else if (low.includes('deep') || low.includes('chill')) {
          filtered = defaultTracks.filter(t => t.moods && t.moods.includes('chill'));
        } else if (low.includes('восточн')) {
          filtered = defaultTracks.filter(t => /miyagi|xcho|jony|jah|hammali|navai|andro/i.test(t.artist));
        } else if (low.includes('phonk') || low.includes('драйв')) {
          filtered = defaultTracks.filter(t => t.moods && (t.moods.includes('drive') || t.moods.includes('energy')));
        } else if (low.includes('зарубеж')) {
          filtered = defaultTracks.filter(t => t.category === 'world');
        }
        state.queue = filtered.length > 0 ? filtered : [...defaultTracks];
        state.queueIndex = 0;
        loadAndPlay(state.queue[0], pl.name);
        showToast(`Плейлист «${pl.name}» (${state.queue.length} треков)`);
      });
      playlistsContainer.appendChild(pCard);
    });
  }

  // 12. Modal Player Controls
  miniPlayerOpenArea.addEventListener('click', () => {
    triggerHaptic();
    fullPlayerModal.classList.add('open');
  });

  closeFullPlayerBtn.addEventListener('click', () => {
    triggerHaptic();
    fullPlayerModal.classList.remove('open');
  });

  modalBackdrop.addEventListener('click', () => {
    fullPlayerModal.classList.remove('open');
  });

  miniPlayBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    togglePlay();
  });

  miniNextBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    playNext();
  });

  fullPlayBtn.addEventListener('click', () => togglePlay());
  prevBtn.addEventListener('click', () => playPrev());
  nextBtn.addEventListener('click', () => playNext());

  shuffleBtn.addEventListener('click', () => {
    triggerHaptic();
    state.isShuffle = !state.isShuffle;
    shuffleBtn.classList.toggle('active', state.isShuffle);
    showToast(state.isShuffle ? 'Случайный порядок включен' : 'Случайный порядок выключен');
  });

  repeatBtn.addEventListener('click', () => {
    triggerHaptic();
    state.isRepeat = !state.isRepeat;
    repeatBtn.classList.toggle('active', state.isRepeat);
    showToast(state.isRepeat ? 'Повтор трека включен' : 'Повтор трека выключен');
  });

  // 13. Pro Free Features: Send to Telegram Chat for background play
  sendToChatBtn.addEventListener('click', async () => {
    triggerHaptic('heavy');
    if (!state.currentTrack) return;

    const userId = tg?.initDataUnsafe?.user?.id;
    showToast('🚀 Отправляем трек вам в чат...');

    try {
      const res = await fetch('/api/send_to_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          track: state.currentTrack
        })
      });

      if (res.ok) {
        showToast('✅ Трек отправлен в чат! Слушайте в фоне с выключенным экраном');
      } else {
        showToast('ℹ️ Откройте чат с ботом @music_abdu_bot, чтобы прослушать трек');
      }
    } catch (e) {
      showToast('ℹ️ Трек готов для отправки в бот @music_abdu_bot');
    }
  });

  downloadMp3Btn.addEventListener('click', () => {
    triggerHaptic('medium');
    if (!state.currentTrack) return;
    showToast('⬇️ Скачивание трека началось...');
    const link = document.createElement('a');
    link.href = state.currentTrack.streamUrl || `/api/stream?id=${encodeURIComponent(state.currentTrack.id)}`;
    link.download = `${state.currentTrack.artist} - ${state.currentTrack.title}.mp3`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // 14. PC Desktop Keyboard Shortcuts (Space = Play/Pause, Esc = Close Modal, Arrows = Seek)
  window.addEventListener('keydown', (e) => {
    if (document.activeElement === searchInput) return;
    if (e.code === 'Space') {
      e.preventDefault();
      togglePlay();
    } else if (e.code === 'ArrowRight') {
      if (audio.duration) {
        audio.currentTime = Math.min(audio.duration, audio.currentTime + 10);
      }
    } else if (e.code === 'ArrowLeft') {
      if (audio.duration) {
        audio.currentTime = Math.max(0, audio.currentTime - 10);
      }
    } else if (e.code === 'Escape') {
      fullPlayerModal.classList.remove('open');
    }
  });

  // 15. Initial Render
  checkUserAccess();
  renderHomeHits();
  renderChart();
  favCountBadge.textContent = `${state.favorites.length} треков`;
  fetchLiveDailyMusic();
});
