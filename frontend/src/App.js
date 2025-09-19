import React, { useState, useEffect } from 'react';
import { Heart, X, Star, Users, Play, ChevronDown } from 'lucide-react';
import './App.css';

// 模擬動漫資料
const mockAnimeData = [
  {
    id: 1,
    title: '鬼滅之刃',
    cover: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=400&fit=crop',
    episodes: 44,
    rating: 8.7,
    viewers: 2500000,
    genres: ['動作', '超自然', '歷史'],
    description: '在大正時期的日本，少年炭治郎為了拯救變成鬼的妹妹，踏上了成為鬼殺隊成員的道路。憑藉著堅強的意志和水之呼吸劍術，他將面對各種強大的鬼怪，展開一場關於親情、友情與正義的史詩冒險。',
    platforms: ['Netflix', 'Crunchyroll'],
    reason: '基於你喜歡的動作和超自然元素，這部作品有精彩的戰鬥場面和深刻的情感故事。'
  },
  {
    id: 2,
    title: '進擊的巨人',
    cover: 'https://images.unsplash.com/photo-1606041008023-472dfb5e530f?w=300&h=400&fit=crop',
    episodes: 87,
    rating: 9.0,
    viewers: 3200000,
    genres: ['動作', '劇情', '黑暗'],
    description: '人類居住在高牆內，對抗著神秘的巨人威脅。艾倫、三笠和阿爾敏踏上了探索真相的旅程，但他們發現的真相比想像中更加殘酷和複雜。',
    platforms: ['Netflix', 'Funimation'],
    reason: '這部作品擁有複雜的世界觀和令人震撼的劇情轉折，適合喜歡深度故事的觀眾。'
  },
  {
    id: 3,
    title: '你的名字',
    cover: 'https://images.unsplash.com/photo-1551269901-5c5e14c25df7?w=300&h=400&fit=crop',
    episodes: 1,
    rating: 8.4,
    viewers: 1800000,
    genres: ['浪漫', '超自然', '劇情'],
    description: '兩個陌生的高中生透過神秘的身體交換現象相遇，展開了一段跨越時空的愛情故事。當他們試圖尋找彼此時，卻發現命運早已將他們的人生緊緊相繫。',
    platforms: ['Netflix', 'Prime Video'],
    reason: '如果你喜歡浪漫和超自然元素的結合，這部電影會帶給你深刻的感動。'
  },
  {
    id: 4,
    title: '咒術迴戰',
    cover: 'https://images.unsplash.com/photo-1612198188060-c7c2a3b66eae?w=300&h=400&fit=crop',
    episodes: 24,
    rating: 8.6,
    viewers: 2100000,
    genres: ['動作', '超自然', '學校'],
    description: '虎杖悠仁無意中吞下了詛咒之王宿儺的手指，從此踏入了咒術師的世界。在東京咒術高等專門學校，他將學習如何控制體內的力量。',
    platforms: ['Crunchyroll', 'Netflix'],
    reason: '現代設定的超自然戰鬥動漫，擁有獨特的咒術系統和精彩的角色設計。'
  },
  {
    id: 5,
    title: '間諜過家家',
    cover: 'https://images.unsplash.com/photo-1583623025817-d180a2221d0a?w=300&h=400&fit=crop',
    episodes: 25,
    rating: 8.8,
    viewers: 2800000,
    genres: ['喜劇', '動作', '家庭'],
    description: '頂級間諜「黃昏」為了執行任務必須組建一個假家庭，他收養了能讀心的女孩安妮亞，並與殺手約兒假結婚。',
    platforms: ['Crunchyroll', 'Netflix'],
    reason: '輕鬆幽默的家庭喜劇，平衡了動作和溫馨的日常。安妮亞的可愛表情讓人忍俊不禁。'
  }
];

const seasons = [
  '2025-1月', '2025-4月', '2025-7月', '2025-10月',
  '2024-10月', '2024-7月', '2024-4月', '2024-1月'
];

function App() {
  const [currentView, setCurrentView] = useState('home'); // 'home', 'recommendations', 'myArea'
  const [favorites, setFavorites] = useState([]);
  const [dislikes, setDislikes] = useState([]);
  const [currentRecommendations, setCurrentRecommendations] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  
  // 表單狀態
  const [selectedSeason, setSelectedSeason] = useState('2025-1月');
  const [recommendCount, setRecommendCount] = useState(5);
  const [description, setDescription] = useState('');
  const [useFavorites, setUseFavorites] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

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
  const handleGenerateRecommendations = () => {
    setIsGenerating(true);
    // 模擬API調用延遲
    setTimeout(() => {
      const filteredAnime = mockAnimeData.filter(anime => !dislikes.includes(anime.id));
      setCurrentRecommendations(filteredAnime.slice(0, recommendCount));
      setCurrentCardIndex(0);
      setCurrentView('recommendations');
      setIsGenerating(false);
    }, 2000);
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
    <div className="home-page">
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
                  onChange={(e) => setSelectedSeason(e.target.value)}
                  className="form-select"
                >
                  {seasons.map(season => (
                    <option key={season} value={season}>
                      {season}
                    </option>
                  ))}
                </select>
                <ChevronDown className="select-icon" />
              </div>
            </div>

            {/* 推薦數量 */}
            <div className="form-group">
              <label className="form-label">推薦數量 (1-10部)</label>
              <input
                type="number"
                min="1"
                max="10"
                value={recommendCount}
                onChange={(e) => setRecommendCount(Number(e.target.value))}
                className="form-input"
                placeholder="輸入想要的推薦數量"
              />
            </div>

            {/* 描述輸入 */}
            <div className="form-group">
              <label className="form-label">動漫偏好描述</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="form-textarea"
                placeholder="描述你想看的動漫類型、劇情偏好等..."
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
              onClick={handleGenerateRecommendations}
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
        <div className="empty-state">
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
      <div className="recommendations-page">
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
            {/* 操作提示 */}
            {currentCardIndex === 0 && (
              <div className="hint-overlay">
                ← → 鍵盤切換 | 滑動瀏覽
              </div>
            )}

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
                    {/* 封面圖 */}
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

                    {/* 卡片內容 */}
                    <div className="card-content">
                      <h3 className="anime-title">{anime.title}</h3>
                      
                      <div className="anime-stats">
                        <span>📺 {anime.episodes} 集</span>
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
                          className={`action-btn dislike-btn ${
                            dislikes.includes(anime.id) ? 'active' : ''
                          }`}
                        >
                          <X className="btn-icon" />
                          <span>{dislikes.includes(anime.id) ? '已標記' : '不喜歡'}</span>
                        </button>
                        <button
                          onClick={() => handleLike(anime)}
                          className={`action-btn like-btn ${
                            favorites.find(fav => fav.id === anime.id) ? 'active' : ''
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

            {/* 左右箭頭按鈕 */}
            {currentCardIndex > 0 && (
              <button
                onClick={goToPrevious}
                className="arrow-btn left-arrow"
                title="上一部 (←)"
              >
                ←
              </button>
            )}
            {currentCardIndex < currentRecommendations.length - 1 && (
              <button
                onClick={goToNext}
                className="arrow-btn right-arrow"
                title="下一部 (→)"
              >
                →
              </button>
            )}
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
    <div className="my-area-page">
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
                    📺 {anime.episodes} 集 • 👥 {(anime.viewers / 1000000).toFixed(1)}M
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
  switch(currentView) {
    case 'recommendations':
      return <RecommendationsView />;
    case 'myArea':
      return <MyAreaView />;
    default:
      return <HomePage />;
  }
}

export default App;