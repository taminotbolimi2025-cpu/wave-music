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

  // Curated Real Tracks (12 guaranteed cached hits)
  const defaultTracks = [
    {
      id: '4EfM6rPmxow',
      title: 'Minor',
      artist: 'MiyaGi & Andy Panda',
      cover: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400',
      duration: '2:56'
    },
    {
      id: 'nidQCt_HEsY',
      title: 'I Got Love',
      artist: 'Miyagi & Эндшпиль',
      cover: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400',
      duration: '4:35'
    },
    {
      id: 'j5cNhjG6iGs',
      title: 'Останься образом',
      artist: 'MACAN',
      cover: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400',
      duration: '3:12'
    },
    {
      id: '7LcZzCPCuvg',
      title: 'По барам',
      artist: 'ANNA ASTI',
      cover: 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400',
      duration: '3:58'
    },
    {
      id: 'p39HcuQNlg4',
      title: 'Прятки',
      artist: 'HammAli & Navai',
      cover: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400',
      duration: '3:10'
    },
    {
      id: 'fHI8X4OXluQ',
      title: 'Blinding Lights',
      artist: 'The Weeknd',
      cover: 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400',
      duration: '3:20'
    },
    {
      id: 'x1XuN5Rq2ws',
      title: 'Ты и Я',
      artist: 'Xcho',
      cover: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400',
      duration: '2:45'
    },
    {
      id: 'yM1QjdoLmxQ',
      title: 'Комета',
      artist: 'JONY',
      cover: 'https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=400',
      duration: '2:38'
    },
    {
      id: 'UJ3COIHd954',
      title: 'Captain',
      artist: 'Miyagi',
      cover: 'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=400',
      duration: '3:40'
    },
    {
      id: 'Rif-RTvmmss',
      title: 'Starboy',
      artist: 'The Weeknd ft. Daft Punk',
      cover: 'https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=400',
      duration: '3:50'
    },
    {
      id: 'wjj2upnfBI0',
      title: 'Lovely',
      artist: 'Billie Eilish & Khalid',
      cover: 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400',
      duration: '3:20'
    },
    {
      id: 'tR1ECf4sEpw',
      title: 'Lose Yourself',
      artist: 'Eminem',
      cover: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400',
      duration: '5:26'
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
    const streamUrl = `/api/stream?id=${encodeURIComponent(streamId)}`;
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
    console.warn('Audio stream error:', err);
    state.isPlaying = false;
    updatePlayPauseState(false);
    if (err && err.code === 4) {
      showToast('⚠️ Формат не поддерживается, пробуем следующий...', 2500);
    } else {
      showToast('⚠️ Ошибка сети, переход к следующему...', 2500);
    }
    setTimeout(() => playNext(), 2000);
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
    showToast('Волна настраивается...');
    try {
      const res = await fetch(`/api/wave?mood=${state.currentMood}`);
      if (res.ok) {
        const data = await res.json();
        if (data.tracks && data.tracks.length > 0) {
          state.queue = data.tracks;
          state.queueIndex = 0;
          loadAndPlay(state.queue[0], `Моя Волна • ${state.currentMood}`);
          return;
        }
      }
    } catch (err) {
      console.warn('Backend wave endpoint offline, using local smart stream:', err);
    }

    // Fallback to internal smart stream
    state.queue = [...defaultTracks].sort(() => Math.random() - 0.5);
    state.queueIndex = 0;
    loadAndPlay(state.queue[0], 'Моя Волна');
  }

  // 8. Search Functionality
  let searchTimeout = null;
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
    searchTimeout = setTimeout(() => executeSearch(q), 400);
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
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        searchLoader.style.display = 'none';
        renderTrackList(data.tracks || [], searchResultsList, 'Поиск: ' + query);
        return;
      }
    } catch (e) {
      console.warn('Search API fallback:', e);
    }

    // Fallback local fuzzy search
    searchLoader.style.display = 'none';
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
  let liveChartTracks = [...defaultTracks];
  let liveReleaseTracks = [...defaultTracks];

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

    // Playlists Grid
    const playlists = [
      { name: 'Хиты 2026', count: '100 треков', img: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=200' },
      { name: 'Кальянный Рэп', count: '50 треков', img: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=200' },
      { name: 'Deep & Chill House', count: '80 треков', img: 'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=200' },
      { name: 'Восточный Вайб', count: '65 треков', img: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=200' }
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
      pCard.addEventListener('click', () => {
        triggerHaptic();
        showToast(`Загружен плейлист: ${pl.name}`);
        state.queue = [...liveChartTracks].sort(() => Math.random() - 0.5);
        state.queueIndex = 0;
        loadAndPlay(state.queue[0], pl.name);
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

  // 14. Initial Render
  renderHomeHits();
  renderChart();
  favCountBadge.textContent = `${state.favorites.length} треков`;
  fetchLiveDailyMusic();
});
