import { useState, useEffect, useRef } from 'react';
import { Heart, X, Star, Users, Play, ChevronDown } from 'lucide-react';
import './App.css';

// 定義前端顯示用的季節列表（用月份顯示）
const displaySeasons = [
  { value: 'random', label: '🎲 隨機推薦' },  // 預設為隨機推薦
  { value: '2025-Fall', label: '2025-10月' },
  { value: '2025-Summer', label: '2025-7月' },
  { value: '2025-Spring', label: '2025-4月' },
  { value: '2025-Winter', label: '2025-1月' },
  { value: '2024-Fall', label: '2024-10月' },
  { value: '2024-Summer', label: '2024-7月' },
  { value: '2024-Spring', label: '2024-4月' },
  { value: '2024-Winter', label: '2024-1月' }
];

// 簡化的季節處理函數
const toBackendFormat = (displaySeason) => {
  console.log('toBackendFormat input:', displaySeason);
  
  // 處理隨機推薦的情況
  if (displaySeason === 'random') {
    console.log('Random recommendation selected');
    return '';  // 返回空字符串表示不指定季度
  }
  
  // 直接返回，因為value已經是正確的格式
  return displaySeason;
};

// 奶茶色系主題
const milkTeaTheme = {
  // 主背景：淺奶茶漸層
  background: 'linear-gradient(135deg, #F3E5D4 0%, #E6D5C3 50%, #D4C4B0 100%)',
  // 主要按鈕：深奶茶色
  accent: '#967259',
  // 按鈕懸停：更深的奶茶色
  accentHover: '#7D5F4C',
  // 輔助色系
  colors: {
    // 輸入框背景：淺米色
    inputBg: '#FFF9F0',
    // 輸入框邊框：淺奶茶色
    inputBorder: '#D4C4B0',
    // 標籤背景：淺褐色
    tagBg: '#E6D5C3',
    // 標籤文字：深褐色
    tagText: '#6B4423',
    // 卡片背景：純白帶透明度
    cardBg: 'rgba(255, 255, 255, 0.9)',
    // 強調文字：深咖啡色
    emphasizedText: '#5C3C24'
  }
};



function App() {
  const [currentView, setCurrentView] = useState('home'); // 'home', 'recommendations', 'myArea'
  const [favorites, setFavorites] = useState([]);
  const [dislikes, setDislikes] = useState([]);
  const [currentRecommendations, setCurrentRecommendations] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);

  // 表單狀態
  const [selectedSeason, setSelectedSeason] = useState('random');  // 初始為隨機推薦
  const [internalSeason, setInternalSeason] = useState('');  // 初始為空，表示不指定季度
  const [recommendCount, setRecommendCount] = useState(5);
  const [description, setDescription] = useState('');
  const [useFavorites, setUseFavorites] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // 當選擇的季節改變時，更新內部季節格式
  useEffect(() => {
    console.log('Selected season changed:', selectedSeason);
    const converted = toBackendFormat(selectedSeason);
    console.log('Converted to backend format:', converted);
    setInternalSeason(converted);
  }, [selectedSeason]);
  
  // 創建 ref 來存儲 textarea 的引用
  const descriptionRef = useRef(null);
  const recommendCountRef = useRef(null);

  // 在生成推薦時使用 ref 的值
  const handleGenerateRecommendationsWithRef = async () => {  // 添加 async
    let newRecommendCount = 5; // 默認值
    let currentDescription = ''; // 保存當前描述

    // 獲取描述文字
    if (descriptionRef.current) {
      currentDescription = descriptionRef.current.value;
      // 同步更新狀態（雖然這次不依賴它）
      setDescription(currentDescription);
    }

    // 更新 recommendCount 狀態為當前輸入框的值
    if (recommendCountRef.current) {
      const value = parseInt(recommendCountRef.current.value);
      if (!isNaN(value) && value >= 1 && value <= 10) {
        newRecommendCount = value;
      }
    }

    // 更新 recommendCount 狀態
    setRecommendCount(newRecommendCount);

    // 確保更新輸入框的顯示值
    if (recommendCountRef.current) {
      recommendCountRef.current.value = String(newRecommendCount);
    }

    // 直接調用生成函數，並傳遞當前描述
    await handleGenerateRecommendations(newRecommendCount, currentDescription);
  };



  // 載入本地存儲的收藏
  useEffect(() => {
    const savedFavorites = localStorage.getItem('anime-favorites');
    const savedDislikes = localStorage.getItem('anime-dislikes');

    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
    if (savedDislikes) {
      setDislikes(JSON.parse(savedDislikes));
    }
  }, []);

  // 保存收藏到本地存儲
  useEffect(() => {
    localStorage.setItem('anime-favorites', JSON.stringify(favorites));
  }, [favorites]);

  useEffect(() => {
    localStorage.setItem('anime-dislikes', JSON.stringify(dislikes));
  }, [dislikes]);

  // 處理推薦生成
  const handleGenerateRecommendations = async (count, currentDescription = '') => {
    setIsGenerating(true);
    try {
      console.log('開始從API獲取數據...', '當前選擇的季度:', selectedSeason);
      console.log('Preparing request with season:', selectedSeason);
      console.log('Internal season format:', internalSeason);
      console.log('當前描述文字:', currentDescription);

      const requestData = {
        count: count || recommendCount,
        season: internalSeason,  // 使用內部存儲的後端格式
        description: currentDescription.trim(),  // 使用傳入的描述文字而不是狀態
        useFavorites: useFavorites,
        favorites: useFavorites ? favorites : [] // 只有在勾選使用專區時才傳送收藏資料
      };
      console.log('發送請求數據:', requestData);
      
      const response = await fetch(`http://localhost:5000/api/anime/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      console.log('API響應狀態:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('從API獲取的原始數據:', data);
      
      if (!Array.isArray(data)) {
        throw new Error('API返回的數據格式不正確');
      }
      
      if (data.length === 0) {
        throw new Error('API返回的數據為空');
      }
      
      // 過濾掉不喜歡的動漫
      const filteredAnime = data.filter(anime => !dislikes.includes(anime.id));
      console.log('過濾後的動漫數據:', filteredAnime);
      
      setCurrentRecommendations(filteredAnime);
      setCurrentCardIndex(0);
      setCurrentView('recommendations');
    } catch (error) {
      console.error('獲取動漫數據時出錯:', error);
      alert(`API請求失敗: ${error.message}`);
      setCurrentRecommendations([]);
      setCurrentCardIndex(0);
    } finally {
      setIsGenerating(false);
    }
  };

  // 處理喜歡/不喜歡
  const handleLike = (anime) => {
    if (favorites.find(fav => fav.id === anime.id)) {
      setFavorites(favorites.filter(fav => fav.id !== anime.id));
    } else {
      setFavorites([...favorites, anime]);
    }
  };

  const handleDislike = (animeId) => {
    if (dislikes.includes(animeId)) {
      setDislikes(dislikes.filter(id => id !== animeId));
    } else {
      setDislikes([...dislikes, animeId]);
    }
  };

  const removeFavorite = (animeId) => {
    setFavorites(favorites.filter(fav => fav.id !== animeId));
  };


  // 主頁面組件
  const HomePage = () => (
    <div className="home-page" style={{ background: milkTeaTheme.background }}>
      <div className="container">
        <h1 className="main-title">
          🎌 動漫推薦 Agent
        </h1>

        <div className="form-container">
          <div className="form-content">
            {/* 季度選擇 */}
            <div className="form-group">
              <label className="form-label">選擇季度</label>
              <div className="select-container">
                <select
                  value={selectedSeason}
                  onChange={(e) => {
                    console.log('Dropdown selection changed to:', e.target.value);
                    setSelectedSeason(e.target.value);
                  }}
                  className="form-select"
                >
                  {displaySeasons.map(season => (
                    <option key={season.value} value={season.value}>
                      {season.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="select-icon" />
              </div>
            </div>

            {/* 推薦數量 */}
            <div className="form-group">
              <label className="form-label">推薦數量 (1-10部)</label>
              <textarea
                ref={recommendCountRef}
                defaultValue={recommendCount}
                className="form-textarea"
                placeholder="輸入想要的推薦數量 (1-10)"
                autoComplete="off"
                rows={2}
                style={{ resize: 'none' }}
              />
            </div>

            {/* 描述輸入 */}
            <div className="form-group">
              <label className="form-label">動漫偏好描述</label>
              <textarea
                ref={descriptionRef}
                defaultValue={description}
                className="form-textarea"
                placeholder="描述你想看的動漫類型、劇情偏好等..."
                autoComplete="off"
                rows={4}
                style={{ resize: 'none' }}
              />
            </div>

            {/* 收藏推薦選項 */}
            <div className="checkbox-group">
              <input
                type="checkbox"
                id="useFavorites"
                checked={useFavorites}
                onChange={(e) => setUseFavorites(e.target.checked)}
                className="form-checkbox"
              />
              <label htmlFor="useFavorites" className="checkbox-label">
                根據我的專區收藏推薦 ({favorites.length} 部收藏)
              </label>
            </div>

            {/* 生成按鈕 */}
            <button
              onClick={handleGenerateRecommendationsWithRef}
              disabled={isGenerating}
              className="generate-btn"
            >
              {isGenerating ? (
                <span>
                  <div className="spinner"></div>
                  生成推薦中...
                </span>
              ) : (
                <span>🎯 開始生成推薦</span>
              )}
            </button>
          </div>
        </div>

        {/* 導航按鈕 */}
        <div className="nav-section">
          <button
            onClick={() => setCurrentView('myArea')}
            className="nav-btn"
          >
            <Heart className="nav-icon" />
            <span>我的專區 ({favorites.length})</span>
          </button>
        </div>
      </div>
    </div>
  );

  // 推薦介面組件
  const RecommendationsView = () => {
    const [touchStartX, setTouchStartX] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState(0);

    // 鍵盤事件監聽
    useEffect(() => {
      const handleKeyPress = (e) => {
        // 如果焦點在輸入元素上，不處理鍵盤事件
        const activeElement = document.activeElement;
        if (activeElement && (
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          activeElement.tagName === 'SELECT' ||
          activeElement.isContentEditable
        )) {
          return;
        }

        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          goToPrevious();
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          goToNext();
        } else if (e.key === 'Escape') {
          setCurrentView('home');
        }
      };

      window.addEventListener('keydown', handleKeyPress);

      return () => {
        window.removeEventListener('keydown', handleKeyPress);
      };
    });

    if (currentRecommendations.length === 0) {
      return (
        <div className="empty-state" style={{ background: milkTeaTheme.background }}>
          <div className="empty-content">
            <h2>推薦完成！</h2>
            <button
              onClick={() => setCurrentView('home')}
              className="back-btn"
            >
              返回主頁
            </button>
          </div>
        </div>
      );
    }

    const goToPrevious = () => {
      if (currentCardIndex > 0) {
        setCurrentCardIndex(currentCardIndex - 1);
      }
    };

    const goToNext = () => {
      if (currentCardIndex < currentRecommendations.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1);
      }
    };

    const handleTouchStart = (e) => {
      setTouchStartX(e.touches[0].clientX);
      setIsDragging(true);
    };

    const handleTouchMove = (e) => {
      if (!isDragging || touchStartX === null) return;
      const currentX = e.touches[0].clientX;
      const diff = currentX - touchStartX;
      setDragOffset(diff);
    };

    const handleTouchEnd = () => {
      if (Math.abs(dragOffset) > 100) {
        if (dragOffset > 0) {
          goToPrevious();
        } else {
          goToNext();
        }
      }
      setIsDragging(false);
      setTouchStartX(null);
      setDragOffset(0);
    };

    return (
      <div className="recommendations-page" style={{ background: milkTeaTheme.background }}>
        <div className="recommendations-container">
          {/* 標題與導航 */}
          <div className="rec-header">
            <button
              onClick={() => setCurrentView('home')}
              className="back-btn-small"
            >
              ← 返回
            </button>
            <h1 className="rec-title">推薦結果</h1>
            <div className="esc-hint">ESC 返回</div>
          </div>

          {/* 進度指示器 */}
          <div className="progress-section">
            <div className="progress-text">
              {currentCardIndex + 1} / {currentRecommendations.length}
            </div>

            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${((currentCardIndex + 1) / currentRecommendations.length) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* 卡片容器 */}
          <div className="cards-container">


            {/* 推薦卡片 */}
            <div
              className="cards-wrapper"
              style={{
                transform: `translateX(calc(-${currentCardIndex * 100}% + ${isDragging ? dragOffset : 0}px))`
              }}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
            >
              {currentRecommendations.map((anime) => (
                <div key={anime.id} className="anime-card">
                  <div className="card-inner">
                    {/* 左側封面圖 */}
                    <div className="card-cover">
                      <img
                        src={anime.cover}
                        alt={anime.title}
                        className="cover-image"
                      />
                      <div className="rating-badge">
                        <Star className="star-icon" />
                        <span>{anime.rating}</span>
                      </div>
                    </div>

                    {/* 右側卡片內容 */}
                    <div className="card-content">
                      <h3 className="anime-title">{anime.title}</h3>

                      <div className="anime-stats">
                        <span className="season-tag">🗓️ {anime.season}</span>
                        <span className="viewers">
                          <Users className="users-icon" />
                          <span>{(anime.viewers / 1000000).toFixed(1)}M</span>
                        </span>
                      </div>

                      <div className="genres">
                        {anime.genres.map(genre => (
                          <span key={genre} className="genre-tag">
                            {genre}
                          </span>
                        ))}
                      </div>

                      <p className="anime-description">
                        {anime.description}
                      </p>

                      <div className="platforms-section">
                        <div className="platforms-header">
                          <Play className="play-icon" />
                          <span>播放平台</span>
                        </div>
                        <div className="platforms-list">
                          {anime.platforms.map(platform => (
                            <span key={platform} className="platform-tag">
                              {platform}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="reason-section">
                        <div className="reason-header">🤖 推薦原因</div>
                        <p className="reason-text">{anime.reason}</p>
                      </div>

                      {/* 操作按鈕 */}
                      <div className="action-buttons">
                        <button
                          onClick={() => handleDislike(anime.id)}
                          className={`action-btn dislike-btn ${dislikes.includes(anime.id) ? 'active' : ''
                            }`}
                        >
                          <X className="btn-icon" />
                          <span>{dislikes.includes(anime.id) ? '已標記' : '不喜歡'}</span>
                        </button>
                        <button
                          onClick={() => handleLike(anime)}
                          className={`action-btn like-btn ${favorites.find(fav => fav.id === anime.id) ? 'active' : ''
                            }`}
                        >
                          <Heart className={`btn-icon ${favorites.find(fav => fav.id === anime.id) ? 'filled' : ''}`} />
                          <span>{favorites.find(fav => fav.id === anime.id) ? '已收藏' : '喜歡'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>


          </div>

          {/* 底部操作提示 */}
          <div className="bottom-hints">
            <p>🖱️ 滑動 | ⌨️ ←→ 鍵盤切換 </p>
            <p>可隨時標記喜歡或不喜歡的動漫</p>
          </div>
        </div>
      </div>
    );
  };

  // 我的專區組件
  const MyAreaView = () => (
    <div className="my-area-page" style={{ background: milkTeaTheme.background }}>
      <div className="my-area-container">
        <div className="my-area-header">
          <h1 className="my-area-title">我的專區</h1>
          <button
            onClick={() => setCurrentView('home')}
            className="back-btn-small"
          >
            返回主頁
          </button>
        </div>

        {favorites.length === 0 ? (
          <div className="empty-favorites">
            <Heart className="empty-icon" />
            <p className="empty-title">還沒有收藏的動漫</p>
            <p className="empty-subtitle">開始推薦並收藏你喜歡的動漫吧！</p>
          </div>
        ) : (
          <div className="favorites-grid">
            {favorites.map(anime => (
              <div key={anime.id} className="favorite-card">
                <div className="favorite-cover">
                  <img
                    src={anime.cover}
                    alt={anime.title}
                    className="favorite-image"
                  />
                  <button
                    onClick={() => removeFavorite(anime.id)}
                    className="remove-btn"
                  >
                    <X className="remove-icon" />
                  </button>
                  <div className="favorite-rating">
                    <Star className="star-small" />
                    <span>{anime.rating}</span>
                  </div>
                </div>

                <div className="favorite-info">
                  <h3 className="favorite-title">{anime.title}</h3>
                  <div className="favorite-stats">
                    🗓️ {anime.season} • 👥 {(anime.viewers / 1000000).toFixed(1)}M
                  </div>
                  <div className="favorite-genres">
                    {anime.genres.slice(0, 3).map(genre => (
                      <span key={genre} className="favorite-genre">
                        {genre}
                      </span>
                    ))}
                  </div>
                  <p className="favorite-desc">
                    {anime.description.slice(0, 100)}...
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  // 主渲染
  switch (currentView) {
    case 'recommendations':
      return <RecommendationsView />;
    case 'myArea':
      return <MyAreaView />;
    default:
      return <HomePage />;
  }
}

export default App;