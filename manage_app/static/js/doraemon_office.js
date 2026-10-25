    function extractYouTubeId(urlOrId) {

        if (!urlOrId) return '3S6R-nOA2eY';

        const str = String(urlOrId).trim();

        const match = str.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);

        if (match && match[1]) {

            return match[1];

        }

        if (/^[\w-]{11}$/.test(str)) {

            return str;

        }

        return '3S6R-nOA2eY';

    }



    // =========================================================================

    // TEXT-TO-SPEECH VIETNAMESE (GIỌNG NỮ MIỀN NAM THẬT 100%)

    // =========================================================================

    window.speakVietnamese = function(text, onDone) {

        if (!text) {

            if (onDone) onDone();

            return;

        }



        // 1. ƯU TIÊN HÀNG ĐẦU: Phát audio giọng nữ tiếng Việt chuẩn từ endpoint /api/chief-secretary/tts

        try {

            if (window._currentCoTamAudio) {

                try {

                    window._currentCoTamAudio.pause();

                    window._currentCoTamAudio.currentTime = 0;

                } catch(e) {}

            }



            const cleanText = text.replace(/[\r\n]+/g, ' ').trim();

            const audioUrl = '/api/chief-secretary/tts?text=' + encodeURIComponent(cleanText);

            const audio = new Audio(audioUrl);

            window._currentCoTamAudio = audio;



            let finished = false;

            const finish = () => {

                if (!finished) {

                    finished = true;

                    window._currentCoTamAudio = null;

                    if (onDone) onDone();

                }

            };



            audio.onended = finish;

            audio.onerror = (e) => {

                console.warn("[TTS Audio] Audio endpoint gặp sự cố, chuyển sang Web SpeechSynthesis:", e);

                fallbackSpeechSynthesis(cleanText, finish);

            };



            const playPromise = audio.play();

            if (playPromise !== undefined) {

                playPromise.catch((err) => {

                    console.warn("[TTS Audio] Autoplay bị chặn bởi trình duyệt, fallback sang Web SpeechSynthesis:", err);

                    fallbackSpeechSynthesis(cleanText, finish);

                });

            }

            return;

        } catch (err) {

            console.warn("[TTS Audio] Lỗi khởi tạo audio:", err);

            fallbackSpeechSynthesis(text, onDone);

        }

    };



    function fallbackSpeechSynthesis(text, onDone) {

        if (!('speechSynthesis' in window)) {

            if (onDone) onDone();

            return;

        }

        try {

            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);

            utterance.lang = 'vi-VN';



            const voices = window.speechSynthesis.getVoices();

            const viVoices = voices.filter(v => 

                (v.lang && (v.lang.startsWith('vi') || v.lang.includes('VIE'))) || 

                (v.name && (v.name.toLowerCase().includes('vietnam') || v.name.toLowerCase().includes('vietnamese') || v.name.toLowerCase().includes('tiếng việt')))

            );



            let chosenVoice = viVoices.find(v => 

                v.name.toLowerCase().includes('south') || 

                v.name.toLowerCase().includes('miền nam') || 

                v.name.toLowerCase().includes('hoaimy') || 

                v.name.toLowerCase().includes('linh') || 

                v.name.toLowerCase().includes('female')

            );

            if (!chosenVoice && viVoices.length > 0) chosenVoice = viVoices[0];

            if (chosenVoice) utterance.voice = chosenVoice;



            utterance.pitch = 1.15;

            utterance.rate = 0.95;

            utterance.onend = () => { if (onDone) onDone(); };

            utterance.onerror = () => { if (onDone) onDone(); };



            window.speechSynthesis.speak(utterance);

        } catch (err) {

            console.warn("fallbackSpeechSynthesis exception:", err);

            if (onDone) onDone();

        }

    }



/**

 * DORAEMON 3D JAPANESE EXECUTIVE VIRTUAL OFFICE - HB MIND HEADQUARTERS

 * - Authentic, Warm & Luxurious Modern Japanese Corporate Architecture

 * - Realistic Desks with Open Legroom Underneath (Characters sit ON chairs, NOT on top of desks!)

 * - Correct Forward Arm Biomechanics (Arms reach forward onto desks/keyboards, NEVER backwards)

 * - Overhead Stretching towards ceiling

 * - CEO Bắc Nguyễn: Tailored Black Suit, White Shirt, Navy Tie, iPad, Document Dossiers

 *   + Sitting naturally on Executive Leather Chair with open knee space under desk

 *   + Floating Badge at y = 4.3 (never obscuring CEO face/glasses)

 * - AI Assistants (Doraemon, Shizuka, Suneo, Gian, Dorami, Dekisugi, etc.):

 *   + Seated comfortably ON the chairs with legs extending into desk knee well

 *   + Floating Badges with DOUBLE-SIZED subtitle text (36px font)

 *   + Aisle waypoint corridor navigation (never walking through furniture)

 *   + Deep Work mode with 💡 lightbulb & typing sound ("cạch cạch...")

 *   + 5s CEO Reporting & 20s Team Meetings

 * - Ceiling Lanterns: Suspended seamlessly from Ceiling (y = 10.0) with ceiling canopy mounts

 * - LIGHT SWITCH & PHAN ĐINH TÙNG BIRTHDAY PARTY:

 *   + Wall Light Switch fixture at (-16.7, 2.2, -10.0)

 *   + CEO walks to switch, flips lights OFF

 *   + Office lighting smoothly dims by 80%

 *   + Phan Đinh Tùng's hit song "Khúc Hát Mừng Sinh Nhật" plays via Web Audio API

 *   + Assistant brings Birthday Cake with lit candles to conference table

 *   + Candle PointLight flickers warmly, illuminating the dark conference table

 *   + Random Birthday Star is crowned with rainbow Party Hat

 *   + Team members gather, clapping rhythmically around the cake

 *   + After 30s: Lights restore to 100%, normal BGM resumes, everyone returns to desks

 */



(function () {

    'use strict';



    // PRELOAD AVATAR CIO BẮC NGUYỄN TOÀN CỤC ĐỂ ĐẢM BẢO LUÔN SẴN SÀNG

    const cioGlobalAvatar = new Image();

    cioGlobalAvatar.src = '/static/images/cio_bac_nguyen.png';



    function roundRect(ctx, x, y, width, height, radius) {

        if (typeof radius === 'number') {

            radius = { tl: radius, tr: radius, br: radius, bl: radius };

        } else {

            radius = Object.assign({ tl: 0, tr: 0, br: 0, bl: 0 }, radius);

        }

        ctx.beginPath();

        ctx.moveTo(x + radius.tl, y);

        ctx.lineTo(x + width - radius.tr, y);

        ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);

        ctx.lineTo(x + width, y + height - radius.br);

        ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);

        ctx.lineTo(x + radius.bl, y + height);

        ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);

        ctx.lineTo(x, y + radius.tl);

        ctx.quadraticCurveTo(x, y, x + radius.tl, y);

        ctx.closePath();

    }



    // Helper: Rounded Box Geometry (Extrude with 2D rounded rectangle & bevel)

    function createRoundedBoxGeometry(w, h, d, r = 0.15, s = 4) {

        r = Math.min(r, w * 0.35, d * 0.35, h * 0.35);

        const shape = new THREE.Shape();

        const halfW = w / 2;

        const halfD = d / 2;

        shape.moveTo(-halfW + r, -halfD);

        shape.lineTo(halfW - r, -halfD);

        shape.quadraticCurveTo(halfW, -halfD, halfW, -halfD + r);

        shape.lineTo(halfW, halfD - r);

        shape.quadraticCurveTo(halfW, halfD, halfW - r, halfD);

        shape.lineTo(-halfW + r, halfD);

        shape.quadraticCurveTo(-halfW, halfD, -halfW, halfD - r);

        shape.lineTo(-halfW, -halfD + r);

        shape.quadraticCurveTo(-halfW, -halfD, -halfW + r, -halfD);



        const extrudeSettings = {

            depth: Math.max(0.02, h - r * 0.4),

            bevelEnabled: true,

            bevelSegments: s,

            steps: 1,

            bevelSize: r * 0.25,

            bevelThickness: r * 0.25

        };

        const geo = new THREE.ExtrudeGeometry(shape, extrudeSettings);

        geo.center();

        geo.rotateX(-Math.PI / 2);

        return geo;

    }



    // =========================================================================

    // 1. MASTER DORAEMON UNIVERSE ROSTER

    // =========================================================================

    const DORAEMON_ROSTER = [

        { key: 'doraemon', name: 'Doraemon', badge: 'Đôrêmon', role: 'Cố vấn Tối cao', avatar: '🐱', color: 0x0284c7, type: 'doraemon' },

        { key: 'shizuka', name: 'Shizuka', badge: 'Xuka', role: 'Trợ lý Pháp chế', avatar: '👧', color: 0xf472b6, type: 'shizuka' },

        { key: 'suneo', name: 'Suneo', badge: 'Xêkô', role: 'Trợ lý Tài chính', avatar: '🦊', color: 0x0d9488, type: 'suneo' },

        { key: 'gian', name: 'Gian', badge: 'Chaien', role: 'Trợ lý Kiểm tra', avatar: '🦁', color: 0xea580c, type: 'gian' },

        { key: 'dorami', name: 'Dorami', badge: 'Đôrêmi', role: 'Trợ lý Công nghệ', avatar: '🎀', color: 0xfacc15, type: 'dorami' },

        { key: 'dekisugi', name: 'Dekisugi', badge: 'Đêkhi', role: 'Trợ lý Nghiên cứu', avatar: '🎓', color: 0x16a34a, type: 'dekisugi' },

        { key: 'jaiko', name: 'Jaiko', badge: 'Chaiko', role: 'Trợ lý Soạn thảo', avatar: '🎨', color: 0xdc2626, type: 'jaiko' },

        { key: 'minidora', name: 'Mini-Dora', badge: 'Dora Mini', role: 'Trợ lý Nhanh nhẹn', avatar: '🔴', color: 0xef4444, type: 'minidora' },

        { key: 'sensei', name: 'Sensei', badge: 'Thầy giáo', role: 'Trợ lý Kỷ luật', avatar: '👓', color: 0x475569, type: 'sensei' },

        { key: 'kaminari', name: 'Kaminari', badge: 'Bác Kaminari', role: 'Trợ lý Trọng tài', avatar: '⚡', color: 0x6d28d9, type: 'kaminari' },

        { key: 'sewashi', name: 'Sewashi', badge: 'Nôbitoru', role: 'Trợ lý Tương lai', avatar: '🚀', color: 0x0284c7, type: 'sewashi' }

    ];



    function normalizeText(text) {

        if (!text) return '';

        return text.toLowerCase()

            .normalize('NFD')

            .replace(/[\u0300-\u036f]/g, '')

            .replace(/[\u0111\u0110]/g, 'd')

            .replace(/[^a-z0-9]/g, '');

    }



    function matchCharacter(nickname, index, usedKeys = []) {

        if (nickname) {

            const clean = normalizeText(nickname);

            if (clean.includes('doremon') || clean.includes('doraemon') || clean.includes('meomay')) return DORAEMON_ROSTER[0];

            if (clean.includes('shizuka') || clean.includes('xuka')) return DORAEMON_ROSTER[1];

            if (clean.includes('suneo') || clean.includes('xeko')) return DORAEMON_ROSTER[2];

            if (clean.includes('gian') || clean.includes('chaien') || clean.includes('jaian')) return DORAEMON_ROSTER[3];

            if (clean.includes('dorami') || clean.includes('doremi')) return DORAEMON_ROSTER[4];

            if (clean.includes('dekisugi') || clean.includes('dekhi')) return DORAEMON_ROSTER[5];

            if (clean.includes('jaiko') || clean.includes('chaiko')) return DORAEMON_ROSTER[6];

            if (clean.includes('minidora') || clean.includes('doramini')) return DORAEMON_ROSTER[7];

            if (clean.includes('sensei') || clean.includes('thaygiao')) return DORAEMON_ROSTER[8];

            if (clean.includes('kaminari') || clean.includes('backaminari')) return DORAEMON_ROSTER[9];

            if (clean.includes('sewashi') || clean.includes('nobitoru')) return DORAEMON_ROSTER[10];

        }

        for (const char of DORAEMON_ROSTER) {

            if (!usedKeys.includes(char.key)) return char;

        }

        return DORAEMON_ROSTER[index % DORAEMON_ROSTER.length];

    }



    // =========================================================================

    // 1B. DANH SÁCH 10 NHÂN VẬT TRUYỆN CỔ TÍCH VIỆT NAM (THƯ KÝ AI TIN TỨC)

    // =========================================================================

    const FAIRY_TALE_ROSTER = [

        { key: 'thach_sanh', name: 'Thạch Sanh', badge: 'Thư ký Tin tức', role: 'Dũng sĩ Thạch Sanh', avatar: '🏹', color: 0x854d0e, type: 'fairy_tale' },

        { key: 'thanh_giong', name: 'Thánh Gióng', badge: 'Thư ký Tin tức', role: 'Phù Đổng Thiên Vương', avatar: '🐎', color: 0xdc2626, type: 'fairy_tale' },

        { key: 'mai_an_tiem', name: 'Mai An Tiêm', badge: 'Thư ký Tin tức', role: 'Mai An Tiêm', avatar: '🍉', color: 0x059669, type: 'fairy_tale' },

        { key: 'chu_dong_tu', name: 'Chử Đồng Tử', badge: 'Thư ký Tin tức', role: 'Chử Đồng Tử', avatar: '🛶', color: 0xca8a04, type: 'fairy_tale' },

        { key: 'co_tam', name: 'Cô Tấm', badge: 'Thư ký Tin tức', role: 'Cô Tấm dịu hiền', avatar: '🌸', color: 0xec4899, type: 'fairy_tale' },

        { key: 'cam', name: 'Cám', badge: 'Thư ký Tin tức', role: 'Cám', avatar: '🪞', color: 0x9333ea, type: 'fairy_tale' },

        { key: 'son_tinh', name: 'Sơn Tinh', badge: 'Thư ký Tin tức', role: 'Sơn Tinh (Tản Viên)', avatar: '⛰️', color: 0x15803d, type: 'fairy_tale' },

        { key: 'thuy_tinh', name: 'Thủy Tinh', badge: 'Thư ký Tin tức', role: 'Thủy Tinh', avatar: '🌊', color: 0x1d4ed8, type: 'fairy_tale' },

        { key: 'an_duong_vuong', name: 'An Dương Vương', badge: 'Thư ký Tin tức', role: 'An Dương Vương', avatar: '👑', color: 0x991b1b, type: 'fairy_tale' },

        { key: 'chu_cuoi', name: 'Chú Cuội', badge: 'Thư ký Tin tức', role: 'Chú Cuội', avatar: '🌙', color: 0xa16207, type: 'fairy_tale' }

    ];



    function matchFairyTaleCharacter(nameOrChar, index) {
        if (nameOrChar) {
            const clean = normalizeText(nameOrChar);
            // 1. So khớp chính xác theo key hoặc tên không dấu không khoảng cách
            for (let i = 0; i < FAIRY_TALE_ROSTER.length; i++) {
                const f = FAIRY_TALE_ROSTER[i];
                const fKey = normalizeText(f.key);
                const fName = normalizeText(f.name);
                if (clean === fKey || clean === fName || clean.includes(fKey) || clean.includes(fName)) {
                    return f;
                }
            }
            // 2. Danh mục định danh viết liền không khoảng trắng
            if (clean.includes('thuytinh') || clean.includes('thuy')) return FAIRY_TALE_ROSTER[7];
            if (clean.includes('sontinh') || clean.includes('tanvien')) return FAIRY_TALE_ROSTER[6];
            if (clean.includes('thachsanh') || clean.includes('sanh') || clean.includes('thach')) return FAIRY_TALE_ROSTER[0];
            if (clean.includes('thanhgiong') || clean.includes('giong')) return FAIRY_TALE_ROSTER[1];
            if (clean.includes('antiem') || clean.includes('tiem')) return FAIRY_TALE_ROSTER[2];
            if (clean.includes('dongtu') || clean.includes('chudong')) return FAIRY_TALE_ROSTER[3];
            if (clean.includes('tam')) return FAIRY_TALE_ROSTER[4];
            if (clean.includes('cam')) return FAIRY_TALE_ROSTER[5];
            if (clean.includes('anduong') || clean.includes('thucphan')) return FAIRY_TALE_ROSTER[8];
            if (clean.includes('cuoi')) return FAIRY_TALE_ROSTER[9];
        }
        return FAIRY_TALE_ROSTER[index % FAIRY_TALE_ROSTER.length];
    }

    // =========================================================================

    // 2. BACKGROUND MUSIC & BIRTHDAY SONG (PHAN ĐINH TÙNG) AUDIO SYNTHESIZER

    // =========================================================================

    class JapaneseOfficeAudioPlayer {

        constructor() {

            this.audioCtx = null;

            this.isPlaying = false;

            this.isMuted = false;

            this.currentTrack = 0;

            this.volume = 0.38;

            this.timerId = null;

            this.masterGain = null;

            this.noteIndex = 0;



            // Birthday Mode State & Official Phan Đinh Tùng Birthday Song (30s)

            this.isBirthdayMode = false;

            this.birthdayNoteIndex = 0;

            this.birthdayTimerId = null;

            this.birthdayAudio = new Audio('/static/audio/phan_dinh_tung_birthday.mp3');

            this.birthdayAudio.preload = 'auto';

            this.birthdayAudio.addEventListener('ended', () => {

                if (window.DoraemonOfficeController && window.DoraemonOfficeController.instance) {

                    window.DoraemonOfficeController.instance.endBirthdayParty();

                }

            });



            // Normal BGM Tracks

            this.tracks = [

                // Track 0: Doraemon no Uta (Iconic Theme Song Melody)

                {

                    title: "Doraemon Theme (Piano Chill)",

                    instrument: "piano",

                    tempo: 120,

                    melody: [

                        { f: 392.00, d: 0.32, b: 130.81 },

                        { f: 392.00, d: 0.32 },

                        { f: 329.63, d: 0.32 },

                        { f: 261.63, d: 0.32 },

                        { f: 293.66, d: 0.32, b: 146.83 },

                        { f: 329.63, d: 0.32 },

                        { f: 392.00, d: 0.65, b: 196.00 },

                        { f: 0, d: 0.20 },

                        { f: 440.00, d: 0.32, b: 174.61 },

                        { f: 440.00, d: 0.32 },

                        { f: 392.00, d: 0.32 },

                        { f: 329.63, d: 0.32 },

                        { f: 293.66, d: 0.32, b: 196.00 },

                        { f: 261.63, d: 0.32 },

                        { f: 293.66, d: 0.32 },

                        { f: 329.63, d: 0.65, b: 130.81 },

                        { f: 0, d: 0.20 },

                        { f: 392.00, d: 0.32, b: 130.81 },

                        { f: 440.00, d: 0.32 },

                        { f: 523.25, d: 0.50, b: 174.61 },

                        { f: 493.88, d: 0.32 },

                        { f: 440.00, d: 0.32 },

                        { f: 392.00, d: 0.40, b: 196.00 },

                        { f: 329.63, d: 0.40 },

                        { f: 293.66, d: 0.40 },

                        { f: 329.63, d: 0.35, b: 130.81 },

                        { f: 293.66, d: 0.35 },

                        { f: 261.63, d: 0.85, b: 130.81 },

                        { f: 0, d: 0.50 }

                    ]

                },

                // Track 1: Tokyo Spring (Acoustic Guitar Fingerstyle)

                {

                    title: "Tokyo Spring (Acoustic Guitar)",

                    instrument: "guitar",

                    tempo: 110,

                    melody: [

                        { f: 196.00, d: 0.28, b: 98.00 },

                        { f: 246.94, d: 0.28 },

                        { f: 293.66, d: 0.28 },

                        { f: 392.00, d: 0.55 },

                        { f: 293.66, d: 0.28 },

                        { f: 246.94, d: 0.28 },

                        { f: 185.00, d: 0.28, b: 92.50 },

                        { f: 220.00, d: 0.28 },

                        { f: 293.66, d: 0.28 },

                        { f: 369.99, d: 0.55 },

                        { f: 293.66, d: 0.28 },

                        { f: 220.00, d: 0.28 },

                        { f: 164.81, d: 0.28, b: 82.41 },

                        { f: 196.00, d: 0.28 },

                        { f: 246.94, d: 0.28 },

                        { f: 329.63, d: 0.55 },

                        { f: 246.94, d: 0.28 },

                        { f: 196.00, d: 0.28 },

                        { f: 130.81, d: 0.28, b: 65.41 },

                        { f: 164.81, d: 0.28 },

                        { f: 196.00, d: 0.28 },

                        { f: 261.63, d: 0.70 },

                        { f: 196.00, d: 0.28 },

                        { f: 164.81, d: 0.28 }

                    ]

                },

                // Track 2: Kyoto Zen Garden (Sakura Sakura - Koto & Flute)

                {

                    title: "Kyoto Zen Garden (Koto & Flute)",

                    instrument: "koto",

                    tempo: 75,

                    melody: [

                        { f: 440.00, d: 0.45, b: 110.00 },

                        { f: 440.00, d: 0.45 },

                        { f: 493.88, d: 0.85, b: 110.00 },

                        { f: 440.00, d: 0.45 },

                        { f: 440.00, d: 0.45 },

                        { f: 493.88, d: 0.85, b: 110.00 },

                        { f: 440.00, d: 0.40 },

                        { f: 493.88, d: 0.40 },

                        { f: 523.25, d: 0.40, b: 130.81 },

                        { f: 493.88, d: 0.40 },

                        { f: 440.00, d: 0.40 },

                        { f: 493.88, d: 0.40 },

                        { f: 440.00, d: 0.40 },

                        { f: 349.23, d: 0.40, b: 87.31 },

                        { f: 329.63, d: 0.85, b: 110.00 },

                        { f: 0, d: 0.40 }

                    ]

                },

                // Track 3: Nobita's Daydream (Music Box & Celesta)

                {

                    title: "Nobita's Daydream (Music Box)",

                    instrument: "musicbox",

                    tempo: 90,

                    melody: [

                        { f: 659.25, d: 0.35 },

                        { f: 783.99, d: 0.35 },

                        { f: 987.77, d: 0.35 },

                        { f: 1046.50, d: 0.70 },

                        { f: 783.99, d: 0.35 },

                        { f: 659.25, d: 0.35 },

                        { f: 587.33, d: 0.35 },

                        { f: 698.46, d: 0.35 },

                        { f: 880.00, d: 0.35 },

                        { f: 987.77, d: 0.70 },

                        { f: 783.99, d: 0.35 },

                        { f: 587.33, d: 0.35 },

                        { f: 523.25, d: 0.35 },

                        { f: 659.25, d: 0.35 },

                        { f: 783.99, d: 0.35 },

                        { f: 880.00, d: 0.70 },

                        { f: 659.25, d: 0.35 },

                        { f: 523.25, d: 0.70 }

                    ]

                },

                // Track 4: Anime Focus Beats (Lofi Chill & Rhodes)

                {

                    title: "Anime Focus Beats (Lofi Chill)",

                    instrument: "lofi",

                    tempo: 76,

                    melody: [

                        { f: 329.63, d: 0.45, b: 146.83 },

                        { f: 349.23, d: 0.35 },

                        { f: 440.00, d: 0.45 },

                        { f: 523.25, d: 0.70 },

                        { f: 392.00, d: 0.45, b: 98.00 },

                        { f: 493.88, d: 0.35 },

                        { f: 659.25, d: 0.70 },

                        { f: 293.66, d: 0.45, b: 130.81 },

                        { f: 329.63, d: 0.35 },

                        { f: 392.00, d: 0.45 },

                        { f: 493.88, d: 0.75 },

                        { f: 261.63, d: 0.45, b: 110.00 },

                        { f: 329.63, d: 0.45 },

                        { f: 392.00, d: 0.75 }

                    ]

                }

            ];



            // SPECIAL TRACK: "Khúc Hát Mừng Sinh Nhật" - Phan Đinh Tùng

            this.birthdayMelody = [

                { f: 392.00, d: 0.28, b: 130.81 },

                { f: 523.25, d: 0.28 },

                { f: 523.25, d: 0.28 },

                { f: 523.25, d: 0.28 },

                { f: 493.88, d: 0.28 },

                { f: 440.00, d: 0.28 },

                { f: 392.00, d: 0.45, b: 196.00 },

                { f: 440.00, d: 0.28 },

                { f: 392.00, d: 0.28 },

                { f: 329.63, d: 0.55, b: 130.81 },

                { f: 0, d: 0.15 },



                { f: 392.00, d: 0.28, b: 130.81 },

                { f: 523.25, d: 0.28 },

                { f: 523.25, d: 0.28 },

                { f: 523.25, d: 0.28 },

                { f: 493.88, d: 0.28 },

                { f: 440.00, d: 0.28 },

                { f: 392.00, d: 0.45, b: 196.00 },

                { f: 440.00, d: 0.28 },

                { f: 493.88, d: 0.28 },

                { f: 523.25, d: 0.70, b: 130.81 },

                { f: 0, d: 0.20 },



                { f: 659.25, d: 0.30, b: 164.81 },

                { f: 587.33, d: 0.30 },

                { f: 523.25, d: 0.30 },

                { f: 440.00, d: 0.30, b: 174.61 },

                { f: 392.00, d: 0.30 },

                { f: 523.25, d: 0.60, b: 130.81 },

                { f: 0, d: 0.15 },



                { f: 659.25, d: 0.26, b: 130.81 },

                { f: 659.25, d: 0.26 },

                { f: 659.25, d: 0.26 },

                { f: 659.25, d: 0.35 },

                { f: 587.33, d: 0.26 },

                { f: 523.25, d: 0.26 },

                { f: 587.33, d: 0.55, b: 146.83 },

                { f: 783.99, d: 0.30, b: 196.00 },

                { f: 659.25, d: 0.30 },

                { f: 587.33, d: 0.30 },

                { f: 523.25, d: 0.75, b: 130.81 },

                { f: 0, d: 0.20 },



                { f: 392.00, d: 0.28, b: 130.81 },

                { f: 523.25, d: 0.28 },

                { f: 587.33, d: 0.28 },

                { f: 659.25, d: 0.45, b: 164.81 },

                { f: 659.25, d: 0.28 },

                { f: 587.33, d: 0.28 },

                { f: 523.25, d: 0.28 },

                { f: 587.33, d: 0.60, b: 146.83 },

                { f: 659.25, d: 0.28, b: 130.81 },

                { f: 587.33, d: 0.28 },

                { f: 523.25, d: 0.28 },

                { f: 440.00, d: 0.28, b: 174.61 },

                { f: 523.25, d: 0.95, b: 130.81 },

                { f: 0, d: 0.40 }

            ];

        }



        initContext() {

            if (!this.audioCtx) {

                const AudioContext = window.AudioContext || window.webkitAudioContext;

                if (!AudioContext) return false;

                this.audioCtx = new AudioContext();

                this.masterGain = this.audioCtx.createGain();

                this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : this.volume, this.audioCtx.currentTime);

                this.masterGain.connect(this.audioCtx.destination);

            }

            if (this.audioCtx.state === 'suspended') {

                this.audioCtx.resume();

            }

            return true;

        }



        playNote(freq, duration = 0.5, instrument = "piano", bassFreq = null) {

            if (!this.audioCtx || this.isMuted || freq <= 0) return;

            try {

                const now = this.audioCtx.currentTime;

                const osc = this.audioCtx.createOscillator();

                const gain = this.audioCtx.createGain();



                if (instrument === "koto") {

                    osc.type = "sawtooth";

                    gain.gain.setValueAtTime(0.28 * this.volume, now);

                    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration * 1.8);

                } else if (instrument === "guitar") {

                    osc.type = "triangle";

                    gain.gain.setValueAtTime(0.32 * this.volume, now);

                    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration * 1.5);

                } else if (instrument === "musicbox") {

                    osc.type = "sine";

                    gain.gain.setValueAtTime(0.24 * this.volume, now);

                    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration * 2.2);

                } else {

                    osc.type = "triangle";

                    gain.gain.setValueAtTime(0.001, now);

                    gain.gain.linearRampToValueAtTime(0.32 * this.volume, now + 0.035);

                    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration * 1.4);

                }



                osc.frequency.setValueAtTime(freq, now);

                osc.connect(gain);

                gain.connect(this.masterGain);



                osc.start(now);

                osc.stop(now + duration * 2.2);



                if (bassFreq && bassFreq > 0) {

                    const bassOsc = this.audioCtx.createOscillator();

                    const bassGain = this.audioCtx.createGain();

                    bassOsc.type = "sine";

                    bassOsc.frequency.setValueAtTime(bassFreq, now);

                    bassGain.gain.setValueAtTime(0.20 * this.volume, now);

                    bassGain.gain.exponentialRampToValueAtTime(0.0001, now + duration * 2.0);

                    bassOsc.connect(bassGain);

                    bassGain.connect(this.masterGain);

                    bassOsc.start(now);

                    bassOsc.stop(now + duration * 2.0);

                }

            } catch (e) {}

        }



        playKeyboardClick() {

            if (!this.audioCtx || this.isMuted) return;

            try {

                const now = this.audioCtx.currentTime;

                const osc = this.audioCtx.createOscillator();

                const gain = this.audioCtx.createGain();



                const freq = 2800 + Math.random() * 800;

                osc.type = "square";

                osc.frequency.setValueAtTime(freq, now);



                gain.gain.setValueAtTime(0.08 * this.volume, now);

                gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.025);



                osc.connect(gain);

                gain.connect(this.masterGain);



                osc.start(now);

                osc.stop(now + 0.03);

            } catch (e) {}

        }



        playSwitchClick() {

            if (!this.audioCtx || this.isMuted) return;

            try {

                const now = this.audioCtx.currentTime;

                const osc = this.audioCtx.createOscillator();

                const gain = this.audioCtx.createGain();

                osc.type = "square";

                osc.frequency.setValueAtTime(1200, now);

                osc.frequency.exponentialRampToValueAtTime(300, now + 0.04);

                gain.gain.setValueAtTime(0.18 * this.volume, now);

                gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.05);

                osc.connect(gain);

                gain.connect(this.masterGain);

                osc.start(now);

                osc.stop(now + 0.05);

            } catch (e) {}

        }



        playNextNote() {

            if (!this.isPlaying || this.isBirthdayMode) return;

            const track = this.tracks[this.currentTrack] || this.tracks[0];

            const melody = track.melody;



            if (this.noteIndex >= melody.length) {

                this.noteIndex = 0;

            }



            const item = melody[this.noteIndex];

            this.noteIndex++;



            if (item.f > 0) {

                this.playNote(item.f, item.d, track.instrument, item.b || null);

            }



            const interval = item.d * 1000;

            this.timerId = setTimeout(() => this.playNextNote(), Math.max(120, interval));

        }



        playNextBirthdayNote() {

            if (!this.isBirthdayMode) return;

            const melody = this.birthdayMelody;

            if (this.birthdayNoteIndex >= melody.length) {

                this.birthdayNoteIndex = 0;

            }



            const item = melody[this.birthdayNoteIndex];

            this.birthdayNoteIndex++;



            if (item.f > 0) {

                this.playNote(item.f, item.d, "piano", item.b || null);

            }



            const interval = item.d * 1000;

            this.birthdayTimerId = setTimeout(() => this.playNextBirthdayNote(), Math.max(120, interval));

        }



        startBirthdaySong() {

            this.initContext();

            this.isBirthdayMode = true;

            this.birthdayNoteIndex = 0;

            if (this.timerId) {

                clearTimeout(this.timerId);

                this.timerId = null;

            }



            // Phát bài hát chính thức "Khúc Hát Mừng Sinh Nhật" của ca sĩ Phan Đinh Tùng

            if (this.birthdayAudio) {

                this.birthdayAudio.currentTime = 0;

                this.birthdayAudio.volume = this.isMuted ? 0 : Math.min(1.0, this.volume * 2.5);

                const playPromise = this.birthdayAudio.play();

                if (playPromise !== undefined) {

                    playPromise.catch(err => {

                        console.warn("Audio autoplay policy or blocked, falling back to Web Audio synthesis:", err);

                        this.playNextBirthdayNote();

                    });

                }

            } else {

                this.playNextBirthdayNote();

            }

            this.updateUI();

        }



        stopBirthdaySong() {

            this.isBirthdayMode = false;

            if (this.birthdayAudio) {

                this.birthdayAudio.pause();

                this.birthdayAudio.currentTime = 0;

            }

            if (this.birthdayTimerId) {

                clearTimeout(this.birthdayTimerId);

                this.birthdayTimerId = null;

            }

            if (this.isPlaying) {

                this.playNextNote();

            }

            this.updateUI();

        }



        togglePlay() {

            if (this.isPlaying) this.pause();

            else this.play();

        }



        play() {

            if (!this.initContext()) return;

            this.isPlaying = true;

            this.updateUI();

            if (this.isBirthdayMode) {

                if (!this.birthdayTimerId) this.playNextBirthdayNote();

            } else {

                if (!this.timerId) this.playNextNote();

            }

        }



        pause() {

            this.isPlaying = false;

            if (this.timerId) {

                clearTimeout(this.timerId);

                this.timerId = null;

            }

            if (this.birthdayTimerId) {

                clearTimeout(this.birthdayTimerId);

                this.birthdayTimerId = null;

            }

            this.updateUI();

        }



        selectTrack(index) {

            this.currentTrack = parseInt(index, 10) || 0;

            this.noteIndex = 0;

            if (this.timerId) {

                clearTimeout(this.timerId);

                this.timerId = null;

            }

            if (!this.isPlaying) {

                this.play();

            } else if (!this.isBirthdayMode) {

                this.playNextNote();

            }

            this.updateUI();

        }



        setVolume(val) {

            this.volume = Math.max(0, Math.min(1, parseFloat(val) || 0.38));

            if (this.masterGain && this.audioCtx) {

                this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : this.volume, this.audioCtx.currentTime);

            }

            if (this.birthdayAudio) {

                this.birthdayAudio.volume = this.isMuted ? 0 : Math.min(1.0, this.volume * 2.5);

            }

            this.updateUI();

        }



        toggleMute() {

            this.isMuted = !this.isMuted;

            if (this.masterGain && this.audioCtx) {

                this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : this.volume, this.audioCtx.currentTime);

            }

            if (this.birthdayAudio) {

                this.birthdayAudio.volume = this.isMuted ? 0 : Math.min(1.0, this.volume * 2.5);

            }

            this.updateUI();

        }



        updateUI() {

            const playBtn = document.getElementById('bgmPlayBtn');

            const playIcon = document.getElementById('bgmPlayIcon');

            const playLabel = document.getElementById('bgmPlayLabel');

            const muteIcon = document.getElementById('bgmMuteIcon');

            const waveEl = document.getElementById('bgmWaveIndicator');

            const selectEl = document.getElementById('bgmTrackSelect');



            if (selectEl && selectEl.value != this.currentTrack) {

                selectEl.value = this.currentTrack;

            }



            if (playIcon && playLabel) {

                if (this.isPlaying) {

                    playIcon.className = 'fa-solid fa-pause text-[10px] text-amber-500';

                    playLabel.textContent = 'Tạm dừng';

                    if (playBtn) playBtn.className = 'px-2.5 py-1 text-xs font-semibold rounded-lg bg-amber-50 text-amber-800 border border-amber-300 hover:bg-amber-100 transition flex items-center space-x-1 shadow-2xs';

                } else {

                    playIcon.className = 'fa-solid fa-play text-[10px] text-emerald-600';

                    playLabel.textContent = 'Phát nhạc';

                    if (playBtn) playBtn.className = 'px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition flex items-center space-x-1';

                }

            }



            if (muteIcon) {

                muteIcon.className = this.isMuted ? 'fa-solid fa-volume-xmark text-[11px] text-rose-500' : 'fa-solid fa-volume-high text-[11px] text-slate-700';

            }



            if (waveEl) {

                if (this.isPlaying && !this.isMuted) {

                    waveEl.classList.remove('opacity-40');

                    waveEl.classList.add('opacity-100');

                } else {

                    waveEl.classList.remove('opacity-100');

                    waveEl.classList.add('opacity-40');

                }

            }

        }

    }



    // =========================================================================

    // 3. 3D FLOATING NAME BADGES (BILLBOARD SPRITES)

    // =========================================================================

    const CIO_SLOGANS = [

        "Nghĩ lớn, làm thật, bứt phá nhanh.",

        "Nói ít làm nhiều, mục tiêu là trên hết.",

        "Hành động hôm nay, thành công ngày mai.",

        "Không tìm lý do, chỉ tìm giải pháp.",

        "Khó khăn là thước đo của bản lĩnh.",

        "Áp lực tạo kim cương.",

        "Ngã ở đâu, đứng lên gấp đôi ở đó.",

        "Chưa đạt mục tiêu, chưa dừng bước.",

        "Vượt giới hạn, chạm đỉnh cao.",

        "Làm việc bằng đam mê, trả lời bằng kết quả.",

        "Kỷ luật thép, thành công vàng.",

        "Chung một mục tiêu, vươn tầm cao mới.",

        "Đoàn kết là sức mạnh, quyết tâm là chiến thắng.",

        "Cam kết 100% – Không lùi bước."

    ];



    function createFloatingNameBadge(nameText, roleText, badgeType = 'assistant') {

        const isNobita = (badgeType === true || badgeType === 'nobita');

        const isSecretary = (badgeType === 'secretary');

        const isChiefSecretary = (badgeType === 'chief_secretary');



        const canvas = document.createElement('canvas');

        const mCtx = canvas.getContext('2d');



        let isTwoLines = false;

        let line1 = '';

        let line2 = '';

        let boxInnerW = 540;

        let boxInnerH = 210;



        if (isNobita) {

            canvas.width = 1180;

            canvas.height = 320;

        } else {

            // YÊU CẦU 2 & 7: Co giãn hình chữ nhật tùy theo nội dung chữ để tiết kiệm không gian!

            // Tên nhân vật (Dòng 1): Tăng lên 1.4 lần (36px * 1.4 = 50px)

            const nameFontSize = 50;

            mCtx.font = `bold ${nameFontSize}px "Segoe UI", Arial, sans-serif`;

            const nameW = mCtx.measureText(nameText.toUpperCase()).width;



            // Chữ ở dưới (Dòng 2 - Vai trò/nhiệm vụ): Tăng lên gấp đôi (26px * 2 = 52px)

            const fullRole = roleText || (isSecretary ? 'Thư Ký Tin Tức' : 'Trợ Lý Chuyên Môn');

            let roleFontSize = 52;

            mCtx.font = `bold ${roleFontSize}px "Segoe UI", Arial, sans-serif`;

            let roleW = mCtx.measureText(fullRole).width;



            let maxContentW = Math.max(nameW, roleW);



            if (roleW > 540 && fullRole.includes(' ')) {
                isTwoLines = true;
                roleFontSize = 44;
                mCtx.font = `bold ${roleFontSize}px "Segoe UI", Arial, sans-serif`;
                const words = fullRole.split(' ');
                const mid = Math.ceil(words.length / 2);
                line1 = words.slice(0, mid).join(' ');
                line2 = words.slice(mid).join(' ');
                const w1 = mCtx.measureText(line1).width;
                const w2 = mCtx.measureText(line2).width;
                maxContentW = Math.max(nameW, w1, w2);
            } else {
                line1 = fullRole;
            }

            // Tự động mở rộng khung chữ nhật ôm trọn toàn bộ nội dung, không khống chế giới hạn 860px
            // Padding mỗi bên tối thiểu 70px (tổng cộng +140px) giúp chữ dài không bao giờ bị chạm mép hay tràn
            boxInnerW = Math.max(420, Math.round(maxContentW + 140));
            boxInnerH = isTwoLines ? 260 : 195;

            // Canvas padding thêm bóng đổ
            canvas.width = boxInnerW + 64;
            canvas.height = boxInnerH + 64;
        }

        const ctx = canvas.getContext('2d');

        const w = canvas.width;

        const h = canvas.height;



        const texture = new THREE.CanvasTexture(canvas);

        texture.minFilter = THREE.LinearFilter;



        let currentSloganIndex = Math.floor(Math.random() * CIO_SLOGANS.length);

        let activeSlogan = CIO_SLOGANS[currentSloganIndex];



        function renderBadge() {

            ctx.clearRect(0, 0, w, h);



            if (isNobita) {

                // 1. TẤM ẢNH ĐẠI DIỆN CIO BẮC NGUYỄN: NẰM ĐỨNG VÀ BO BỐN GÓC

                const avatarW = 195;

                const avatarH = 265;

                const avatarX = 24;

                const avatarY = (h - avatarH) / 2;

                const avatarRadius = 24;



                ctx.save();

                ctx.shadowColor = 'rgba(0, 0, 0, 0.65)';

                ctx.shadowBlur = 14;

                ctx.shadowOffsetY = 5;



                roundRect(ctx, avatarX, avatarY, avatarW, avatarH, avatarRadius);



                if (cioGlobalAvatar && cioGlobalAvatar.complete && cioGlobalAvatar.naturalWidth > 0) {

                    ctx.clip();

                    const iw = cioGlobalAvatar.naturalWidth;

                    const ih = cioGlobalAvatar.naturalHeight;

                    const targetAspect = avatarW / avatarH;

                    let cropW, cropH, cropX, cropY;

                    if (iw / ih > targetAspect) {

                        cropH = ih;

                        cropW = ih * targetAspect;

                        cropX = (iw - cropW) / 2;

                        cropY = 0;

                    } else {

                        cropW = iw;

                        cropH = iw / targetAspect;

                        cropX = 0;

                        cropY = (ih - cropH) * 0.12;

                    }

                    ctx.drawImage(cioGlobalAvatar, cropX, cropY, cropW, cropH, avatarX, avatarY, avatarW, avatarH);

                } else {

                    // Fallback màu xanh hoàng gia

                    ctx.fillStyle = '#002e5b';

                    ctx.fill();

                    ctx.fillStyle = '#fde047';

                    ctx.font = 'bold 36px "Segoe UI", Arial, sans-serif';

                    ctx.textAlign = 'center';

                    ctx.textBaseline = 'middle';

                    ctx.fillText('CIO', avatarX + avatarW / 2, avatarY + avatarH / 2);

                }

                ctx.restore();



                // Viền vàng hình chữ nhật bo 4 góc ngoài ảnh đại diện

                ctx.strokeStyle = '#facc15';

                ctx.lineWidth = 6;

                roundRect(ctx, avatarX, avatarY, avatarW, avatarH, avatarRadius);

                ctx.stroke();



                // 2. KHUNG CHỨA CHỮ CIO BẮC NGUYỄN VÀ SLOGAN (NẰM BÊN PHẢI ẢNH)

                const boxX = avatarX + avatarW + 20;

                const boxY = avatarY;

                const boxW = w - boxX - 24;

                const boxH = avatarH;

                const boxCenterX = boxX + boxW / 2;



                ctx.shadowColor = 'rgba(0, 0, 0, 0.65)';

                ctx.shadowBlur = 16;

                ctx.shadowOffsetY = 6;



                const grad = ctx.createLinearGradient(boxX, 0, boxX + boxW, 0);

                grad.addColorStop(0, '#002e5b');

                grad.addColorStop(0.5, '#004b93');

                grad.addColorStop(1, '#002e5b');

                ctx.fillStyle = grad;

                roundRect(ctx, boxX, boxY, boxW, boxH, 24);

                ctx.fill();



                // Viền vàng quanh khung chữ

                ctx.shadowColor = 'transparent';

                ctx.strokeStyle = '#facc15';

                ctx.lineWidth = 6;

                roundRect(ctx, boxX, boxY, boxW, boxH, 24);

                ctx.stroke();



                // Dòng 1: ★ CIO BẮC NGUYỄN ★

                ctx.fillStyle = '#ffffff';

                ctx.font = 'bold 50px "Segoe UI", Arial, sans-serif';

                ctx.textAlign = 'center';

                ctx.textBaseline = 'middle';

                ctx.fillText('★ CIO BẮC NGUYỄN ★', boxCenterX, boxY + 76);



                // Dòng 2: SLOGAN

                const sloganText = `“${activeSlogan}”`;

                let sloganFontSize = 56;

                ctx.font = `bold ${sloganFontSize}px "Segoe UI", Arial, sans-serif`;

                while (ctx.measureText(sloganText).width > (boxW - 48) && sloganFontSize > 34) {

                    sloganFontSize--;

                    ctx.font = `bold ${sloganFontSize}px "Segoe UI", Arial, sans-serif`;

                }

                ctx.fillStyle = '#fde047';

                ctx.fillText(sloganText, boxCenterX, boxY + 180);



            } else {

                // ==================== TRỢ LÝ CHUYÊN MÔN HOẶC THƯ KÝ AI TIN TỨC ====================

                const rx = 32;

                const ry = 32;

                const rw = boxInnerW;

                const rh = boxInnerH;

                const cx = rx + rw / 2;



                ctx.shadowColor = 'rgba(0, 0, 0, 0.28)';

                ctx.shadowBlur = 12;

                ctx.shadowOffsetY = 5;



                if (isChiefSecretary) {

                    // YÊU CẦU ĐẶC BIỆT: TỔNG THƯ KÝ CÔ TẤM

                    // - Nền hình chữ nhật: màu hồng nhạt (#fff0f5 - LavenderBlush / Soft Pink)

                    // - Viền hình chữ nhật: màu hồng cánh sen tinh tế (#f472b6)

                    // - Dải header bar phía trên: màu hồng sen (#ec4899)

                    // - Chữ màu ĐỎ RƯỢU VANG (#800020 - Wine Red / #881337 - Burgundy):

                    //   + Dòng 1 (Tên Tổng Thư Ký): Đỏ rượu vang (#800020)

                    //   + Dòng 2 (Vai trò): Đỏ rượu vang (#881337)

                    ctx.fillStyle = '#fff0f5';

                    roundRect(ctx, rx, ry, rw, rh, 24);

                    ctx.fill();



                    ctx.shadowColor = 'transparent';

                    ctx.strokeStyle = '#f472b6';

                    ctx.lineWidth = 6;

                    roundRect(ctx, rx, ry, rw, rh, 24);

                    ctx.stroke();



                    // Header bar hồng sen nổi bật

                    ctx.fillStyle = '#ec4899';

                    roundRect(ctx, rx, ry, rw, 16, { tl: 24, tr: 24, bl: 0, br: 0 });

                    ctx.fill();



                    // Dòng 1: TÊN TỔNG THƯ KÝ (CHỮ MÀU ĐỎ RƯỢU VANG #800020, TĂNG 1.4 LẦN -> 50px)

                    ctx.fillStyle = '#800020';

                    ctx.font = 'bold 50px "Segoe UI", Arial, sans-serif';

                    ctx.textAlign = 'center';

                    ctx.textBaseline = 'middle';

                    ctx.fillText(nameText.toUpperCase(), cx, ry + 56);



                    // Dòng 2: VAI TRÒ TỔNG THƯ KÝ (CHỮ MÀU ĐỎ RƯỢU VANG #881337)

                    ctx.fillStyle = '#881337';

                    if (isTwoLines) {

                        ctx.font = 'bold 46px "Segoe UI", Arial, sans-serif';

                        ctx.fillText(line1, cx, ry + 128);

                        ctx.fillText(line2, cx, ry + 184);

                    } else {

                        ctx.font = 'bold 52px "Segoe UI", Arial, sans-serif';

                        ctx.fillText(line1, cx, ry + 138);

                    }



                } else if (isSecretary) {

                    // YÊU CẦU 3 (THƯ KÝ AI TIN TỨC):

                    // - Nền hình chữ nhật màu trắng đỏ nhạt (#fff5f5)

                    // - Viền hình chữ nhật màu đỏ (#dc2626)

                    // - Chữ màu đỏ (#991b1b cho tên, #dc2626 cho vai trò)

                    ctx.fillStyle = '#fff5f5';

                    roundRect(ctx, rx, ry, rw, rh, 24);

                    ctx.fill();



                    ctx.shadowColor = 'transparent';

                    ctx.strokeStyle = '#dc2626';

                    ctx.lineWidth = 6;

                    roundRect(ctx, rx, ry, rw, rh, 24);

                    ctx.stroke();



                    // Header bar đỏ nổi bật

                    ctx.fillStyle = '#ef4444';

                    roundRect(ctx, rx, ry, rw, 16, { tl: 24, tr: 24, bl: 0, br: 0 });

                    ctx.fill();



                    // Dòng 1: TÊN THƯ KÝ (CHỮ MÀU ĐỎ ĐẬM, TĂNG 1.4 LẦN -> 50px)

                    ctx.fillStyle = '#991b1b';

                    ctx.font = 'bold 50px "Segoe UI", Arial, sans-serif';

                    ctx.textAlign = 'center';

                    ctx.textBaseline = 'middle';

                    ctx.fillText(nameText.toUpperCase(), cx, ry + 56);



                    // Dòng 2: VAI TRÒ THƯ KÝ (CHỮ MÀU ĐỎ, TĂNG GẤP ĐÔI)

                    ctx.fillStyle = '#dc2626';

                    if (isTwoLines) {

                        ctx.font = 'bold 46px "Segoe UI", Arial, sans-serif';

                        ctx.fillText(line1, cx, ry + 128);

                        ctx.fillText(line2, cx, ry + 184);

                    } else {

                        ctx.font = 'bold 52px "Segoe UI", Arial, sans-serif';

                        ctx.fillText(line1, cx, ry + 138);

                    }



                } else {

                    // TRỢ LÝ CHUYÊN MÔN (DORAEMON & BẠN BÈ):

                    // - Nền trắng (#ffffff)

                    // - Viền xanh đậm (#003b73)

                    // - Chữ xanh đen (#002855 cho tên, #003b73 cho vai trò)

                    ctx.fillStyle = '#ffffff';

                    roundRect(ctx, rx, ry, rw, rh, 24);

                    ctx.fill();



                    ctx.shadowColor = 'transparent';

                    ctx.strokeStyle = '#003b73';

                    ctx.lineWidth = 6;

                    roundRect(ctx, rx, ry, rw, rh, 24);

                    ctx.stroke();



                    // Header bar xanh thương hiệu

                    ctx.fillStyle = '#004b93';

                    roundRect(ctx, rx, ry, rw, 16, { tl: 24, tr: 24, bl: 0, br: 0 });

                    ctx.fill();



                    // Dòng 1: TÊN TRỢ LÝ (CHỮ XANH ĐEN, TĂNG 1.4 LẦN -> 50px)

                    ctx.fillStyle = '#002855';

                    ctx.font = 'bold 50px "Segoe UI", Arial, sans-serif';

                    ctx.textAlign = 'center';

                    ctx.textBaseline = 'middle';

                    ctx.fillText(nameText.toUpperCase(), cx, ry + 56);



                    // Dòng 2: VAI TRÒ TRỢ LÝ (CHỮ XANH ĐEN, TĂNG GẤP ĐÔI)

                    ctx.fillStyle = '#003b73';

                    if (isTwoLines) {

                        ctx.font = 'bold 46px "Segoe UI", Arial, sans-serif';

                        ctx.fillText(line1, cx, ry + 128);

                        ctx.fillText(line2, cx, ry + 184);

                    } else {

                        ctx.font = 'bold 52px "Segoe UI", Arial, sans-serif';

                        ctx.fillText(line1, cx, ry + 138);

                    }

                }

            }



            texture.needsUpdate = true;

        }



        renderBadge();



        if (isNobita) {

            if (!cioGlobalAvatar.complete) {

                cioGlobalAvatar.onload = () => renderBadge();

            }

            setTimeout(() => renderBadge(), 300);

            setTimeout(() => renderBadge(), 1200);



            setInterval(() => {

                let nextIdx;

                do {

                    nextIdx = Math.floor(Math.random() * CIO_SLOGANS.length);

                } while (nextIdx === currentSloganIndex && CIO_SLOGANS.length > 1);

                currentSloganIndex = nextIdx;

                activeSlogan = CIO_SLOGANS[currentSloganIndex];

                renderBadge();

            }, 30000);

        }



        const mat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });

        const sprite = new THREE.Sprite(mat);

        sprite.renderOrder = 999;



        // YÊU CẦU 7: Sprite co giãn tỉ lệ thuận theo kích thước canvas để tiết kiệm không gian!

        if (isNobita) {

            sprite.scale.set(6.0, 1.65, 1.0);

        } else {

            const baseScaleY = isTwoLines ? 1.65 : 1.35;

            const baseScaleX = baseScaleY * (canvas.width / canvas.height);

            sprite.scale.set(baseScaleX, baseScaleY, 1.0);

        }



        // TỐI ƯU HÓA RAYCAST CHO BẢNG TÊN HÌNH CHỮ NHẬT:

        // Cung cấp thuật toán raycast trực tiếp trên mặt phẳng billboard đối diện camera với buffer 25%

        // Đảm bảo click vào bất kỳ góc, cạnh, mép nào của hình chữ nhật đều kích hoạt mở popup 100%!

        sprite.raycast = function(raycaster, intersects) {

            if (!raycaster.camera) return;

            const camera = raycaster.camera;

            const worldPos = new THREE.Vector3();

            this.getWorldPosition(worldPos);



            const worldScale = new THREE.Vector3();

            this.getWorldScale(worldScale);

            const halfW = (worldScale.x * 0.5) * 1.25;

            const halfH = (worldScale.y * 0.5) * 1.25;



            const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);

            const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);



            const vA = worldPos.clone().addScaledVector(right, -halfW).addScaledVector(up, -halfH);

            const vB = worldPos.clone().addScaledVector(right,  halfW).addScaledVector(up, -halfH);

            const vC = worldPos.clone().addScaledVector(right,  halfW).addScaledVector(up,  halfH);

            const vD = worldPos.clone().addScaledVector(right, -halfW).addScaledVector(up,  halfH);



            const hitPoint = new THREE.Vector3();

            let hit = raycaster.ray.intersectTriangle(vA, vB, vC, false, hitPoint);

            if (!hit) {

                hit = raycaster.ray.intersectTriangle(vA, vC, vD, false, hitPoint);

            }



            if (hit) {

                const dist = raycaster.ray.origin.distanceTo(hitPoint);

                if (dist >= raycaster.near && dist <= raycaster.far) {

                    intersects.push({

                        distance: dist,

                        point: hitPoint.clone(),

                        face: null,

                        object: this

                    });

                }

            }

        };



        return sprite;

    }



    // =========================================================================

    // 4. 3D GLOWING LIGHTBULB MODEL (💡 THINKING / DEEP WORK INDICATOR)

    // =========================================================================

    function createThinkingLightbulb() {

        const group = new THREE.Group();

        group.name = 'thinkingLightbulb';



        const bulbMat = new THREE.MeshStandardMaterial({

            color: 0xfef08a,

            emissive: 0xfacc15,

            emissiveIntensity: 0.95,

            roughness: 0.2

        });

        const bulbSphere = new THREE.Mesh(new THREE.SphereGeometry(0.24, 16, 16), bulbMat);

        bulbSphere.position.y = 0.35;

        group.add(bulbSphere);



        const bulbCone = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.25, 12), bulbMat);

        bulbCone.position.y = 0.18;

        bulbCone.rotation.x = Math.PI;

        group.add(bulbCone);



        const baseMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.3 });

        const base = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.16, 12), baseMat);

        base.position.y = 0.05;

        group.add(base);



        const rayMat = new THREE.MeshBasicMaterial({ color: 0xfde047 });

        for (let i = 0; i < 6; i++) {

            const angle = (i * Math.PI * 2) / 6;

            const ray = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.25, 0.04), rayMat);

            ray.position.set(Math.cos(angle) * 0.44, 0.35 + Math.sin(angle) * 0.44, 0);

            ray.rotation.z = angle - Math.PI / 2;

            group.add(ray);

        }



        group.position.set(0, 4.4, 0);

        group.visible = false;

        return group;

    }



    // =========================================================================

    // 5. 3D REALISTIC ERGONOMIC OFFICE CHAIRS

    // =========================================================================

    function buildExecutiveLeatherChair() {

        const chairGroup = new THREE.Group();



        // Chrome 5-star swivel base with caster wheels

        const baseStem = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.45, 8), new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.2 }));

        baseStem.position.y = 0.25;

        chairGroup.add(baseStem);



        for (let i = 0; i < 5; i++) {

            const angle = (i * Math.PI * 2) / 5;

            const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.70, 6), new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9 }));

            leg.rotation.z = Math.PI / 2;

            leg.rotation.y = angle;

            leg.position.set(Math.cos(angle) * 0.35, 0.10, Math.sin(angle) * 0.35);



            const wheel = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 8), new THREE.MeshStandardMaterial({ color: 0x18181b }));

            wheel.position.set(Math.cos(angle) * 0.70, 0.06, Math.sin(angle) * 0.70);

            chairGroup.add(leg, wheel);

        }



        // Thick Black Leather Seat Cushion (Seat surface at y = 0.50m)

        const leatherMat = new THREE.MeshStandardMaterial({ color: 0x1c1917, roughness: 0.45, metalness: 0.1 });

        const seat = new THREE.Mesh(createRoundedBoxGeometry(1.3, 0.18, 1.2, 0.08, 3), leatherMat);

        seat.position.y = 0.46;

        chairGroup.add(seat);



        // High Ergonomic Backrest with Lumbar Curve (at z = -0.55)

        const backrest = new THREE.Mesh(createRoundedBoxGeometry(1.2, 1.4, 0.20, 0.08, 3), leatherMat);

        backrest.position.set(0, 1.25, -0.55);

        backrest.rotation.x = -0.06;

        chairGroup.add(backrest);



        // Headrest

        const headrest = new THREE.Mesh(createRoundedBoxGeometry(0.85, 0.40, 0.18, 0.08, 3), leatherMat);

        headrest.position.set(0, 2.05, -0.62);

        chairGroup.add(headrest);



        // Padded Chrome Armrests

        const armMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 });

        for (let side of [-1, 1]) {

            const armStem = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.45, 0.08), armMat);

            armStem.position.set(side * 0.68, 0.75, -0.10);

            const armPad = new THREE.Mesh(createRoundedBoxGeometry(0.16, 0.06, 0.65, 0.03, 2), leatherMat);

            armPad.position.set(side * 0.68, 0.98, -0.06);

            chairGroup.add(armStem, armPad);

        }



        return chairGroup;

    }



    function buildStandardOfficeChair(meshColor = 0x334155) {

        const chairGroup = new THREE.Group();



        const base = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.38, 8), new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.7 }));

        base.position.y = 0.22;

        chairGroup.add(base);



        for (let i = 0; i < 5; i++) {

            const angle = (i * Math.PI * 2) / 5;

            const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.50, 6), new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.8 }));

            leg.rotation.z = Math.PI / 2;

            leg.rotation.y = angle;

            leg.position.set(Math.cos(angle) * 0.25, 0.08, Math.sin(angle) * 0.25);



            const wheel = new THREE.Mesh(new THREE.SphereGeometry(0.045, 6, 6), new THREE.MeshStandardMaterial({ color: 0x0f172a }));

            wheel.position.set(Math.cos(angle) * 0.50, 0.045, Math.sin(angle) * 0.50);

            chairGroup.add(leg, wheel);

        }



        // Curved Ergonomic Mesh Seat (at y = 0.45m)

        const seatMat = new THREE.MeshStandardMaterial({ color: meshColor, roughness: 0.7 });

        const seat = new THREE.Mesh(createRoundedBoxGeometry(0.85, 0.12, 0.80, 0.06, 2), seatMat);

        seat.position.y = 0.44;



        // Backrest at z = -0.38

        const back = new THREE.Mesh(createRoundedBoxGeometry(0.80, 0.95, 0.10, 0.06, 2), seatMat);

        back.position.set(0, 0.98, -0.38);

        back.rotation.x = -0.06;



        for (let side of [-1, 1]) {

            const arm = new THREE.Mesh(createRoundedBoxGeometry(0.07, 0.04, 0.40, 0.02, 2), new THREE.MeshStandardMaterial({ color: 0x1e293b }));

            arm.position.set(side * 0.44, 0.75, -0.08);

            chairGroup.add(arm);

        }



        chairGroup.add(seat, back);

        return chairGroup;

    }



    // =========================================================================

    // 6. PROCEDURAL TEXTURES (RICH WALNUT, TATAMI, SHOJI, FUJI, WHITEBOARD)

    // =========================================================================

    function createRichWalnutFloorTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        ctx.fillStyle = '#653e20';

        ctx.fillRect(0, 0, 512, 512);



        const plankH = 32;

        for (let y = 0; y < 512; y += plankH) {

            ctx.fillStyle = (y / plankH) % 2 === 0 ? '#5a361a' : '#6c4323';

            ctx.fillRect(0, y, 512, plankH - 2);



            ctx.strokeStyle = 'rgba(40, 20, 10, 0.45)';

            ctx.lineWidth = 1.5;

            ctx.strokeRect(0, y, 512, plankH);



            for (let i = 0; i < 5; i++) {

                ctx.strokeStyle = 'rgba(30, 15, 5, 0.15)';

                ctx.beginPath();

                ctx.moveTo(0, y + i * 6 + 3);

                ctx.lineTo(512, y + i * 6 + 4);

                ctx.stroke();

            }

        }



        const texture = new THREE.CanvasTexture(canvas);

        texture.wrapS = THREE.RepeatWrapping;

        texture.wrapT = THREE.RepeatWrapping;

        return texture;

    }



    function createTatamiWovenTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        ctx.fillStyle = '#8f9660';

        ctx.fillRect(0, 0, 512, 512);



        ctx.fillStyle = '#7a804e';

        for (let y = 0; y < 512; y += 4) {

            ctx.fillRect(0, y, 512, 1.5);

        }

        for (let x = 0; x < 512; x += 16) {

            ctx.fillStyle = 'rgba(100, 110, 60, 0.35)';

            ctx.fillRect(x, 0, 1.5, 512);

        }



        ctx.fillStyle = '#1e293b';

        ctx.fillRect(0, 0, 26, 512);

        ctx.fillRect(486, 0, 26, 512);



        ctx.fillStyle = '#facc15';

        for (let y = 16; y < 512; y += 32) {

            ctx.beginPath();

            ctx.arc(13, y, 3.5, 0, Math.PI * 2);

            ctx.arc(499, y, 3.5, 0, Math.PI * 2);

            ctx.fill();

        }



        const texture = new THREE.CanvasTexture(canvas);

        texture.wrapS = THREE.RepeatWrapping;

        texture.wrapT = THREE.RepeatWrapping;

        return texture;

    }



    function createShojiLatticeTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        ctx.fillStyle = '#fffdf7';

        ctx.fillRect(0, 0, 512, 512);



        ctx.fillStyle = '#5c381e';

        for (let x = 0; x <= 512; x += 64) {

            ctx.fillRect(x - 3, 0, 6, 512);

        }

        for (let y = 0; y <= 512; y += 48) {

            ctx.fillRect(0, y - 2.5, 512, 5);

        }

        ctx.fillRect(0, 0, 12, 512);

        ctx.fillRect(500, 0, 12, 512);

        ctx.fillRect(0, 0, 512, 12);

        ctx.fillRect(0, 500, 512, 12);



        return new THREE.CanvasTexture(canvas);

    }



    function createFujiPanoramaTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 256;

        const ctx = canvas.getContext('2d');



        const grad = ctx.createLinearGradient(0, 0, 0, 256);

        grad.addColorStop(0, '#fbcfe8');

        grad.addColorStop(0.5, '#fed7aa');

        grad.addColorStop(1, '#e0f2fe');

        ctx.fillStyle = grad;

        ctx.fillRect(0, 0, 512, 256);



        ctx.fillStyle = '#ef4444';

        ctx.beginPath();

        ctx.arc(256, 120, 50, 0, Math.PI * 2);

        ctx.fill();



        ctx.fillStyle = '#334155';

        ctx.beginPath();

        ctx.moveTo(70, 256);

        ctx.lineTo(210, 75);

        ctx.lineTo(302, 75);

        ctx.lineTo(442, 256);

        ctx.closePath();

        ctx.fill();



        ctx.fillStyle = '#ffffff';

        ctx.beginPath();

        ctx.moveTo(210, 75);

        ctx.lineTo(302, 75);

        ctx.lineTo(340, 135);

        ctx.lineTo(300, 120);

        ctx.lineTo(270, 140);

        ctx.lineTo(240, 120);

        ctx.lineTo(210, 135);

        ctx.lineTo(172, 135);

        ctx.closePath();

        ctx.fill();



        ctx.strokeStyle = '#4a2c11';

        ctx.lineWidth = 4;

        ctx.beginPath();

        ctx.moveTo(0, 30);

        ctx.quadraticCurveTo(80, 50, 140, 40);

        ctx.stroke();



        ctx.fillStyle = '#fb7185';

        for (let i = 0; i < 30; i++) {

            const bx = 20 + i * 4.5 + Math.sin(i) * 12;

            const by = 35 + Math.cos(i) * 14;

            ctx.beginPath();

            ctx.arc(bx, by, 3.8, 0, Math.PI * 2);

            ctx.fill();

        }



        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';

        ctx.fillRect(0, 224, 512, 32);

        ctx.fillStyle = '#ffffff';

        ctx.font = 'bold 13px sans-serif';

        ctx.textAlign = 'center';

        ctx.fillText('HB MIND • TOKYO JAPANESE ARTIFICIAL INTELLIGENCE HEADQUARTERS', 256, 245);



        return new THREE.CanvasTexture(canvas);

    }



    function createWhiteboardTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 256;

        const ctx = canvas.getContext('2d');



        ctx.fillStyle = '#f8fafc';

        ctx.fillRect(0, 0, 512, 256);



        ctx.strokeStyle = '#94a3b8';

        ctx.lineWidth = 6;

        ctx.strokeRect(0, 0, 512, 256);



        ctx.fillStyle = '#004b93';

        ctx.font = 'bold 16px sans-serif';

        ctx.fillText('CHIẾN LƯỢC TRỢ LÝ CHUYÊN MÔN (HB MIND 2026)', 24, 36);



        ctx.fillStyle = '#e0f2fe';

        ctx.strokeStyle = '#0284c7';

        ctx.lineWidth = 2;

        ctx.fillRect(24, 60, 120, 50);

        ctx.strokeRect(24, 60, 120, 50);

        ctx.fillStyle = '#0369a1';

        ctx.font = 'bold 11px sans-serif';

        ctx.fillText('Doraemon AI', 36, 85);

        ctx.fillText('Vertex Search', 36, 100);



        ctx.fillStyle = '#fef3c7';

        ctx.strokeStyle = '#d97706';

        ctx.fillRect(180, 60, 120, 50);

        ctx.strokeRect(180, 60, 120, 50);

        ctx.fillStyle = '#92400e';

        ctx.fillText('Google Drive', 192, 85);

        ctx.fillText('48 Thư mục', 192, 100);



        ctx.fillStyle = '#dcfce7';

        ctx.strokeStyle = '#16a34a';

        ctx.fillRect(340, 60, 140, 50);

        ctx.strokeRect(340, 60, 140, 50);

        ctx.fillStyle = '#15803d';

        ctx.fillText('Chính sách Thuế', 352, 85);

        ctx.fillText('NĐ 253/2026/NĐ-CP', 352, 100);



        ctx.strokeStyle = '#64748b';

        ctx.lineWidth = 2;

        ctx.beginPath();

        ctx.moveTo(144, 85);

        ctx.lineTo(180, 85);

        ctx.moveTo(300, 85);

        ctx.lineTo(340, 85);

        ctx.stroke();



        ctx.fillStyle = '#fef08a';

        ctx.fillRect(30, 140, 70, 70);

        ctx.fillStyle = '#854d0e';

        ctx.font = '10px sans-serif';

        ctx.fillText('Nobita CIO', 36, 160);

        ctx.fillText('Chiến lược', 36, 175);



        ctx.fillStyle = '#fbcfe8';

        ctx.fillRect(130, 140, 70, 70);

        ctx.fillStyle = '#9d174d';

        ctx.fillText('Shizuka', 136, 160);

        ctx.fillText('Pháp chế', 136, 175);



        ctx.fillStyle = '#a7f3d0';

        ctx.fillRect(230, 140, 70, 70);

        ctx.fillStyle = '#065f46';

        ctx.fillText('Internet', 236, 160);

        ctx.fillText('Grounding', 236, 175);



        return new THREE.CanvasTexture(canvas);

    }



    function createTvStandbyTexture(videoTitle = '') {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 320;

        const ctx = canvas.getContext('2d');



        // Deep modern obsidian gradient

        const grad = ctx.createLinearGradient(0, 0, 512, 320);

        grad.addColorStop(0, '#020617');

        grad.addColorStop(0.5, '#0f172a');

        grad.addColorStop(1, '#020617');

        ctx.fillStyle = grad;

        ctx.fillRect(0, 0, 512, 320);



        // Subtle carbon grid lines

        ctx.strokeStyle = 'rgba(30, 41, 59, 0.6)';

        ctx.lineWidth = 1;

        for (let x = 0; x < 512; x += 32) {

            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 320); ctx.stroke();

        }

        for (let y = 0; y < 320; y += 32) {

            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke();

        }



        // Red YouTube Badge

        ctx.fillStyle = '#ef4444';

        ctx.beginPath();

        if (ctx.roundRect) ctx.roundRect(220, 65, 72, 48, 14);

        else ctx.rect(220, 65, 72, 48);

        ctx.fill();



        // Play triangle

        ctx.fillStyle = '#ffffff';

        ctx.beginPath();

        ctx.moveTo(250, 77);

        ctx.lineTo(268, 89);

        ctx.lineTo(250, 101);

        ctx.closePath();

        ctx.fill();



        // Header Title

        ctx.fillStyle = '#f8fafc';

        ctx.font = 'bold 20px sans-serif';

        ctx.textAlign = 'center';

        ctx.fillText('HB MIND - SMART TV ENTERTAINMENT', 256, 155);



        ctx.fillStyle = '#94a3b8';

        ctx.font = '13px sans-serif';

        if (videoTitle) {

            ctx.fillStyle = '#38bdf8';

            ctx.font = 'bold 15px sans-serif';

            ctx.fillText('ĐANG PHÁT: ' + videoTitle.toUpperCase(), 256, 195);

        } else {

            ctx.fillText('Chọn bài hát & bấm "Phát" trên thanh công cụ để chiếu video', 256, 190);

        }



        // Bottom status bar

        ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';

        ctx.fillRect(0, 275, 512, 45);

        ctx.fillStyle = '#10b981';

        ctx.beginPath();

        ctx.arc(36, 298, 5, 0, Math.PI * 2);

        ctx.fill();

        ctx.fillStyle = '#cbd5e1';

        ctx.font = 'bold 12px sans-serif';

        ctx.textAlign = 'left';

        ctx.fillText('SAN SANG KET NOI YOUTUBE STREAMING (75" 4K UHD)', 50, 302);



        return new THREE.CanvasTexture(canvas);

    }



    function createGlossyTileFloorTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        // Base luxury architectural slate grey

        ctx.fillStyle = '#64748b';

        ctx.fillRect(0, 0, 512, 512);



        // 4x4 square tiles (each 128x128px)

        const tiles = 4;

        const tileSize = 512 / tiles;



        for (let ty = 0; ty < tiles; ty++) {

            for (let tx = 0; tx < tiles; tx++) {

                const x0 = tx * tileSize;

                const y0 = ty * tileSize;

                const x1 = x0 + tileSize;

                const y1 = y0 + tileSize;



                // Tile surface with soft cloud / polished porcelain marbling

                const tileGrad = ctx.createLinearGradient(x0, y0, x1, y1);

                tileGrad.addColorStop(0, '#788292');

                tileGrad.addColorStop(0.5, '#6b7484');

                tileGrad.addColorStop(1, '#5d6676');

                ctx.fillStyle = tileGrad;

                ctx.fillRect(x0 + 2, y0 + 2, tileSize - 4, tileSize - 4);



                // Subtle organic marble clouds on each tile

                ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';

                ctx.beginPath();

                ctx.arc(x0 + 40, y0 + 45, 26, 0, Math.PI * 2);

                ctx.fill();

                ctx.beginPath();

                ctx.arc(x0 + 85, y0 + 80, 34, 0, Math.PI * 2);

                ctx.fill();



                // Top and Left beveled highlight (glossy ceramic bevel look)

                ctx.strokeStyle = 'rgba(255, 255, 255, 0.40)';

                ctx.lineWidth = 1.5;

                ctx.beginPath();

                ctx.moveTo(x0 + 2, y1 - 3);

                ctx.lineTo(x0 + 2, y0 + 2);

                ctx.lineTo(x1 - 3, y0 + 2);

                ctx.stroke();



                // Bottom and Right beveled shadow

                ctx.strokeStyle = 'rgba(15, 23, 42, 0.55)';

                ctx.lineWidth = 1.5;

                ctx.beginPath();

                ctx.moveTo(x1 - 2, y0 + 3);

                ctx.lineTo(x1 - 2, y1 - 2);

                ctx.lineTo(x0 + 3, y1 - 2);

                ctx.stroke();

            }

        }



        // Clean dark slate grout lines between tiles

        ctx.strokeStyle = '#1e293b';

        ctx.lineWidth = 3.5;

        for (let i = 0; i <= tiles; i++) {

            const p = i * tileSize;

            ctx.beginPath();

            ctx.moveTo(p, 0);

            ctx.lineTo(p, 512);

            ctx.stroke();

            ctx.beginPath();

            ctx.moveTo(0, p);

            ctx.lineTo(512, p);

            ctx.stroke();

        }



        const tex = new THREE.CanvasTexture(canvas);

        tex.wrapS = THREE.RepeatWrapping;

        tex.wrapT = THREE.RepeatWrapping;

        return tex;

    }



    function createVenetianBlindsTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        // Sky & daylight gradient with subtle green garden horizon

        const skyGrad = ctx.createLinearGradient(0, 0, 0, 512);

        skyGrad.addColorStop(0, '#bae6fd');

        skyGrad.addColorStop(0.55, '#f0fdf4');

        skyGrad.addColorStop(1, '#bbf7d0');

        ctx.fillStyle = skyGrad;

        ctx.fillRect(0, 0, 512, 512);



        // Outdoor lush tree silhouettes visible through blinds

        ctx.fillStyle = '#4ade80';

        for (let i = 0; i < 8; i++) {

            ctx.beginPath();

            ctx.arc(40 + i * 65, 470 + Math.sin(i * 1.5) * 15, 60, 0, Math.PI * 2);

            ctx.fill();

        }

        ctx.fillStyle = '#22c55e';

        for (let i = 0; i < 9; i++) {

            ctx.beginPath();

            ctx.arc(15 + i * 60, 490 + Math.cos(i * 1.8) * 12, 45, 0, Math.PI * 2);

            ctx.fill();

        }



        // Horizontal wooden Venetian blinds slats

        const slatSpacing = 16;

        for (let y = 0; y < 512; y += slatSpacing) {

            // Slat shadow

            ctx.fillStyle = 'rgba(28, 16, 8, 0.42)';

            ctx.fillRect(0, y + 10, 512, 4);



            // Slat warm walnut wood

            const slatGrad = ctx.createLinearGradient(0, y, 0, y + 10);

            slatGrad.addColorStop(0, '#784c32');

            slatGrad.addColorStop(0.6, '#5a3622');

            slatGrad.addColorStop(1, '#3e2415');

            ctx.fillStyle = slatGrad;

            ctx.fillRect(0, y, 512, 10);



            // Wood grain highlight

            ctx.fillStyle = 'rgba(255, 237, 213, 0.18)';

            ctx.fillRect(0, y + 1, 512, 1.5);

        }



        // Vertical ladder cords

        ctx.fillStyle = '#29170e';

        for (let x of [64, 160, 256, 352, 448]) {

            ctx.fillRect(x - 1.5, 0, 3, 512);

        }



        const tex = new THREE.CanvasTexture(canvas);

        tex.wrapS = THREE.RepeatWrapping;

        tex.wrapT = THREE.RepeatWrapping;

        return tex;

    }



    function createGlassMindmapTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 1024;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        // Frosted architectural glass panel background

        const grad = ctx.createLinearGradient(0, 0, 1024, 512);

        grad.addColorStop(0, 'rgba(241, 245, 249, 0.96)');

        grad.addColorStop(1, 'rgba(226, 232, 240, 0.94)');

        ctx.fillStyle = grad;

        ctx.fillRect(0, 0, 1024, 512);



        // Subtle grid pattern on glass

        ctx.strokeStyle = 'rgba(203, 213, 225, 0.6)';

        ctx.lineWidth = 1;

        for (let x = 0; x < 1024; x += 32) {

            ctx.beginPath();

            ctx.moveTo(x, 0);

            ctx.lineTo(x, 512);

            ctx.stroke();

        }

        for (let y = 0; y < 512; y += 32) {

            ctx.beginPath();

            ctx.moveTo(0, y);

            ctx.lineTo(1024, y);

            ctx.stroke();

        }



        // Title Header

        ctx.fillStyle = '#0f172a';

        ctx.font = 'bold 28px sans-serif';

        ctx.fillText('HB MIND  STRATEGIC AI ARCHITECTURE & OPERATIONS (2026)', 40, 52);



        ctx.fillStyle = '#475569';

        ctx.font = '16px sans-serif';

        ctx.fillText('Autonomous Executive Agents  News Intelligence  Real-Time Governance', 40, 80);



        // Architecture connecting diagram lines

        ctx.strokeStyle = '#0284c7';

        ctx.lineWidth = 3;

        ctx.setLineDash([8, 6]);

        ctx.beginPath();

        ctx.moveTo(180, 240);

        ctx.lineTo(400, 240);

        ctx.lineTo(620, 180);

        ctx.lineTo(840, 180);

        ctx.moveTo(400, 240);

        ctx.lineTo(620, 340);

        ctx.lineTo(840, 340);

        ctx.stroke();

        ctx.setLineDash([]);



        // Colorful Modern Sticky Notes (Post-it style)

        function drawSticky(x, y, w, h, bg, rot, title, text1, text2) {

            ctx.save();

            ctx.translate(x + w / 2, y + h / 2);

            ctx.rotate(rot);

            // Shadow

            ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';

            ctx.fillRect(-w / 2 + 3, -h / 2 + 3, w, h);

            // Paper

            ctx.fillStyle = bg;

            ctx.fillRect(-w / 2, -h / 2, w, h);

            // Header

            ctx.fillStyle = '#0f172a';

            ctx.font = 'bold 15px sans-serif';

            ctx.fillText(title, -w / 2 + 12, -h / 2 + 26);

            ctx.font = '13px sans-serif';

            ctx.fillStyle = '#334155';

            if (text1) ctx.fillText(text1, -w / 2 + 12, -h / 2 + 50);

            if (text2) ctx.fillText(text2, -w / 2 + 12, -h / 2 + 70);

            ctx.restore();

        }



        drawSticky(60, 170, 180, 120, '#fef08a', -0.04, 'Thư ký AI Tin tức', 'Tự động chạy ngầm', 'Tìm kiếm Google Search');

        drawSticky(310, 170, 190, 120, '#bae6fd', 0.03, 'Gemini 2.5 Engine', 'Tổng hợp tin tức kinh tế', 'Soạn thảo báo cáo chuẩn');

        drawSticky(560, 110, 200, 120, '#fbcfe8', -0.02, 'Xuất File Word (.docx)', 'Lưu: Thư ký tin tức', 'Tự động đặt tên + ngày giờ');

        drawSticky(560, 280, 200, 120, '#a7f3d0', 0.04, 'Họp Giao Ban 12 Ghế', 'Bảng tên mờ dần 10%', 'Tránh vật cản thông minh');

        drawSticky(800, 110, 180, 120, '#fed7aa', 0.02, 'CIO Bắc Nguyễn', 'Điều hành AI tổng thể', 'Sinh nhật & Sự kiện');

        drawSticky(800, 280, 180, 120, '#e9d5ff', -0.03, 'Trợ lý Chuyên môn', 'Gian  Shizuka  Doraemon', 'Tương tác thông tin 1-1');



        return new THREE.CanvasTexture(canvas);

    }



    function createMarbleTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        // Polished White Calacatta Marble background

        const grad = ctx.createLinearGradient(0, 0, 512, 512);

        grad.addColorStop(0, '#f8fafc');

        grad.addColorStop(0.5, '#ffffff');

        grad.addColorStop(1, '#f1f5f9');

        ctx.fillStyle = grad;

        ctx.fillRect(0, 0, 512, 512);



        // Soft organic marble veins

        ctx.strokeStyle = 'rgba(71, 85, 105, 0.22)';

        ctx.lineWidth = 4;

        ctx.beginPath();

        ctx.moveTo(30, 0);

        ctx.bezierCurveTo(150, 120, 80, 260, 220, 380);

        ctx.bezierCurveTo(280, 440, 360, 470, 420, 512);

        ctx.stroke();



        ctx.strokeStyle = 'rgba(148, 163, 184, 0.32)';

        ctx.lineWidth = 2.5;

        ctx.beginPath();

        ctx.moveTo(350, 0);

        ctx.bezierCurveTo(320, 140, 410, 220, 340, 340);

        ctx.bezierCurveTo(300, 400, 210, 460, 160, 512);

        ctx.stroke();



        // Subtle gold-bronze feather veins

        ctx.strokeStyle = 'rgba(180, 140, 80, 0.18)';

        ctx.lineWidth = 2;

        ctx.beginPath();

        ctx.moveTo(0, 220);

        ctx.bezierCurveTo(140, 180, 280, 260, 512, 210);

        ctx.stroke();



        return new THREE.CanvasTexture(canvas);

    }



    function createFlutedWoodTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 256;

        canvas.height = 256;

        const ctx = canvas.getContext('2d');



        ctx.fillStyle = '#1c1008';

        ctx.fillRect(0, 0, 256, 256);



        // Fluted vertical wood slats with 3D cylindrical lighting gradient

        const slatWidth = 16;

        for (let x = 0; x < 256; x += slatWidth) {

            const grad = ctx.createLinearGradient(x, 0, x + slatWidth - 3, 0);

            grad.addColorStop(0, '#2d180d');

            grad.addColorStop(0.35, '#6a3c20');

            grad.addColorStop(0.65, '#854b28');

            grad.addColorStop(1, '#2d180d');

            ctx.fillStyle = grad;

            ctx.fillRect(x, 0, slatWidth - 3, 256);



            // Dark groove between slats

            ctx.fillStyle = '#0f0804';

            ctx.fillRect(x + slatWidth - 3, 0, 3, 256);

        }



        const tex = new THREE.CanvasTexture(canvas);

        tex.wrapS = THREE.RepeatWrapping;

        tex.wrapT = THREE.RepeatWrapping;

        return tex;

    }



    function createModernRugTexture() {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 512;

        const ctx = canvas.getContext('2d');



        // Warm neutral greige base

        ctx.fillStyle = '#d5cec4';

        ctx.fillRect(0, 0, 512, 512);



        // Woven crosshatch textile texture

        ctx.fillStyle = 'rgba(255, 255, 255, 0.22)';

        for (let y = 0; y < 512; y += 4) {

            ctx.fillRect(0, y, 512, 1.5);

        }

        ctx.fillStyle = 'rgba(120, 110, 100, 0.16)';

        for (let x = 0; x < 512; x += 4) {

            ctx.fillRect(x, 0, 1.5, 512);

        }



        // Heathered subtle noise flecks

        ctx.fillStyle = 'rgba(160, 148, 136, 0.25)';

        for (let i = 0; i < 600; i++) {

            const rx = Math.random() * 512;

            const ry = Math.random() * 512;

            ctx.fillRect(rx, ry, 2, 2);

        }



        const tex = new THREE.CanvasTexture(canvas);

        tex.wrapS = THREE.RepeatWrapping;

        tex.wrapT = THREE.RepeatWrapping;

        return tex;

    }





    // =========================================================================

    // 7. BIRTHDAY CAKE & CELEBRATION MODELS

    // =========================================================================

    function buildBirthdayCake() {

        const group = new THREE.Group();

        group.name = 'birthdayCakeGroup';



        const standMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, metalness: 0.85, roughness: 0.2 });

        const platter = new THREE.Mesh(new THREE.CylinderGeometry(0.90, 0.85, 0.06, 24), standMat);

        platter.position.y = 0.03;

        group.add(platter);



        const cakeMat1 = new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.6 });

        const tier1 = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.35, 24), cakeMat1);

        tier1.position.y = 0.22;

        group.add(tier1);



        const chocoMat = new THREE.MeshStandardMaterial({ color: 0x451a03, roughness: 0.3 });

        const drip = new THREE.Mesh(new THREE.CylinderGeometry(0.78, 0.78, 0.06, 24), chocoMat);

        drip.position.y = 0.38;

        group.add(drip);



        const cakeMat2 = new THREE.MeshStandardMaterial({ color: 0xfda4af, roughness: 0.5 });

        const tier2 = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 0.30, 20), cakeMat2);

        tier2.position.y = 0.55;

        group.add(tier2);



        const strawMat = new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.4 });

        for (let i = 0; i < 6; i++) {

            const angle = (i * Math.PI * 2) / 6;

            const berry = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.12, 8), strawMat);

            berry.position.set(Math.cos(angle) * 0.32, 0.74, Math.sin(angle) * 0.32);

            group.add(berry);

        }



        const creamMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });

        for (let i = 0; i < 6; i++) {

            const angle = (i * Math.PI * 2) / 6 + Math.PI / 6;

            const cream = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 8), creamMat);

            cream.position.set(Math.cos(angle) * 0.32, 0.73, Math.sin(angle) * 0.32);

            group.add(cream);

        }



        const candleColors = [0x38bdf8, 0xfacc15, 0xec4899, 0x4ade80, 0xa855f7];

        const flameOuterMat = new THREE.MeshBasicMaterial({ color: 0xf97316 });

        const flameInnerMat = new THREE.MeshBasicMaterial({ color: 0xffedd5 });



        for (let i = 0; i < 5; i++) {

            const angle = (i * Math.PI * 2) / 5;

            const candleMat = new THREE.MeshStandardMaterial({ color: candleColors[i] });

            const candle = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.22, 8), candleMat);

            candle.position.set(Math.cos(angle) * 0.18, 0.82, Math.sin(angle) * 0.18);



            const flame = new THREE.Mesh(new THREE.ConeGeometry(0.04, 0.10, 8), flameOuterMat);

            flame.position.set(Math.cos(angle) * 0.18, 0.98, Math.sin(angle) * 0.18);



            const flameInner = new THREE.Mesh(new THREE.ConeGeometry(0.02, 0.06, 8), flameInnerMat);

            flameInner.position.set(Math.cos(angle) * 0.18, 0.96, Math.sin(angle) * 0.18);



            group.add(candle, flame, flameInner);

        }



        const candleLight = new THREE.PointLight(0xffaa22, 2.5, 14);

        candleLight.position.set(0, 1.05, 0);

        candleLight.castShadow = true;

        group.add(candleLight);



        return { group, candleLight };

    }



    function buildPartyHat() {

        const group = new THREE.Group();

        group.name = 'partyHat';



        const coneMat = new THREE.MeshStandardMaterial({ color: 0xf43f5e, roughness: 0.4 });

        const cone = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.55, 12), coneMat);

        cone.position.y = 0.28;



        const pomMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.3 });

        const pompom = new THREE.Mesh(new THREE.SphereGeometry(0.08, 10, 10), pomMat);

        pompom.position.y = 0.58;



        const rim = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.03, 6, 16), pomMat);

        rim.rotation.x = Math.PI / 2;

        rim.position.y = 0.02;



        group.add(cone, pompom, rim);

        return group;

    }



    function createCelebrationBanner(name) {

        const canvas = document.createElement('canvas');

        canvas.width = 512;

        canvas.height = 140;

        const ctx = canvas.getContext('2d');



        const grad = ctx.createLinearGradient(0, 0, 512, 0);

        grad.addColorStop(0, '#f43f5e');

        grad.addColorStop(0.5, '#fb923c');

        grad.addColorStop(1, '#facc15');

        ctx.fillStyle = grad;

        roundRect(ctx, 8, 8, 496, 124, 24);

        ctx.fill();



        ctx.strokeStyle = '#ffffff';

        ctx.lineWidth = 4;

        roundRect(ctx, 8, 8, 496, 124, 24);

        ctx.stroke();



        ctx.fillStyle = '#ffffff';

        ctx.font = 'bold 30px "Segoe UI", Arial, sans-serif';

        ctx.textAlign = 'center';

        ctx.textBaseline = 'middle';

        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';

        ctx.shadowBlur = 6;

        ctx.fillText('🎂 CHÚC MỪNG SINH NHẬT 🎉', 256, 44);



        ctx.font = 'bold 28px "Segoe UI", Arial, sans-serif';

        ctx.fillStyle = '#ffffff';

        ctx.fillText(name.toUpperCase(), 256, 92);



        const texture = new THREE.CanvasTexture(canvas);

        const mat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });

        const sprite = new THREE.Sprite(mat);

        sprite.scale.set(4.6, 1.25, 1.0);

        return sprite;

    }



    // =========================================================================

    // 8. MAIN OFFICE 3D CONTROLLER CLASS

    // =========================================================================

    class Office3D {

        constructor(containerId, onSelectAssistant, onSelectSecretary, onRequestSecretaryReport, onEditSecretary, onEditAssistant) {

            this.containerId = containerId;

            this.container = document.getElementById(containerId);

            this.onSelectAssistant = onSelectAssistant || function () {};

            this.onSelectSecretary = onSelectSecretary || function () {};

            this.onRequestSecretaryReport = onRequestSecretaryReport || function () {};

            this.onEditSecretary = onEditSecretary || function () {};

            this.onEditAssistant = onEditAssistant || function () {};

            this.secretariesList = [];

            this.scene = null;

            this.camera = null;

            this.renderer = null;

            this.raycaster = new THREE.Raycaster();

            this.mouse = new THREE.Vector2();

            this.characters = [];

            this.nobita = null;

            this.takeCopterPropellers = [];

            this.animationFrameId = null;

            this.clock = new THREE.Clock();

            this.isDragging = false;

            this.prevMousePos = { x: 0, y: 0 };

            this.cameraTarget = new THREE.Vector3(0, 1.5, 0);

            this.cameraRadius = 38;

            this.cameraAngleH = Math.PI / 4 + 0.12;

            this.cameraAngleV = Math.PI / 5.2;

            this.clickableObjects = [];



            this.ambientLight = null;

            this.sunLight = null;

            this.deskLight = null;

            this.meetingLight = null;

            this.fillLight = null;

            this.currentLightFactor = 1.0;

            this.targetLightFactor = 1.0;



            this.isBirthdayActive = false;

            this.birthdayStage = 'idle';

            this.birthdayTimer = 0;

            this.birthdayStar = null;

            this.cakeBearer = null;

            this.birthdayCakeObj = null;

            this.candleLight = null;

            this.partyHat = null;

            this.celebrationBanner = null;

            this.lightSwitchLever = null;



            this.isMeetingActive = false;

            this.currentTheme = 'japanese';

            try {

                this.currentTheme = localStorage.getItem('doraemon_office_theme') || 'japanese';

            } catch (e) {}

            this.wallSconceLights = [];

            this.environmentGroup = null;

            this.tvScreenMesh = null;

            this.tvGroup = null;

            this.isVideoPlaying = false;

            this.isDancingActive = false;

            this.danceTimer = 0;

            this.videoOverlayEl = null;

            this.currentVideoId = '3S6R-nOA2eY';

            this.wasBgmPlayingBeforeVideo = false;

            this.assistantsData = [];

            this.secretariesData = [];



            this.meetingTime = 0;

            this.meetingTimer = 0;



            this.audioPlayer = new JapaneseOfficeAudioPlayer();

            this.isVoiceMuted = false;

        }



        init(assistants = [], secretaries = [], chiefSecretary = null) {

            if (!this.container) {

                this.container = document.getElementById(this.containerId);

            }

            if (!this.container || typeof THREE === 'undefined') return;

            this.chiefSecretary = chiefSecretary || window.__lastChiefConfig;

            this.cleanup();



            const width = this.container.clientWidth || 900;

            const height = this.container.clientHeight || 620;



            this.scene = new THREE.Scene();

            this.scene.background = new THREE.Color(0xd8cbba);

            this.scene.fog = new THREE.FogExp2(0xd8cbba, 0.007);



            this.camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 350);

            this.updateCameraPosition();



            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });

            this.renderer.setSize(width, height);

            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

            this.renderer.shadowMap.enabled = true;

            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

            this.container.innerHTML = '';

            this.container.appendChild(this.renderer.domElement);



            this.assistantsData = assistants;

            this.secretariesData = secretaries;

            try {

                this.currentTheme = localStorage.getItem('doraemon_office_theme') || 'japanese';

            } catch (e) {}

            this.wallSconceLights = [];

            this.setupLights();



            this.environmentGroup = new THREE.Group();

            this.scene.add(this.environmentGroup);



            this.buildCurrentTheme();

            this.createVideoOverlay();

            this.buildNobitaExecutiveZone();

            this.buildAssistants(assistants, secretaries, this.chiefSecretary);

            this.setupEventListeners();

            this.animate();



            this.audioPlayer.play();

            const startAudioOnFirstInteraction = () => {

                if (this.audioPlayer && !this.audioPlayer.isPlaying) {

                    this.audioPlayer.play();

                }

                window.removeEventListener('click', startAudioOnFirstInteraction);

                window.removeEventListener('mousemove', startAudioOnFirstInteraction);

                window.removeEventListener('keydown', startAudioOnFirstInteraction);

            };

            window.addEventListener('click', startAudioOnFirstInteraction, { once: true });

            window.addEventListener('mousemove', startAudioOnFirstInteraction, { once: true });

            window.addEventListener('keydown', startAudioOnFirstInteraction, { once: true });

        }



        setupLights() {

            this.ambientLight = new THREE.AmbientLight(0xffecd2, 0.75);

            this.scene.add(this.ambientLight);



            this.sunLight = new THREE.DirectionalLight(0xfff6e6, 0.95);

            this.sunLight.position.set(22, 30, 18);

            this.sunLight.castShadow = true;

            this.sunLight.shadow.mapSize.width = 2048;

            this.sunLight.shadow.mapSize.height = 2048;

            this.sunLight.shadow.camera.near = 0.5;

            this.sunLight.shadow.camera.far = 80;

            this.sunLight.shadow.camera.left = -22;

            this.sunLight.shadow.camera.right = 22;

            this.sunLight.shadow.camera.top = 22;

            this.sunLight.shadow.camera.bottom = -22;

            this.sunLight.shadow.bias = -0.0004;

            this.scene.add(this.sunLight);



            this.fillLight = new THREE.DirectionalLight(0xdbeafe, 0.35);

            this.fillLight.position.set(-20, 16, -16);

            this.scene.add(this.fillLight);



            this.deskLight = new THREE.PointLight(0xfef08a, 0.40, 16);

            this.deskLight.position.set(0, 5.5, -2.5);

            this.scene.add(this.deskLight);



            this.meetingLight = new THREE.PointLight(0xfde68a, 0.65, 14);

            this.meetingLight.position.set(9.5, 5.5, -8.5);

            this.scene.add(this.meetingLight);

        }



        buildCurrentTheme() {

            if (!this.environmentGroup) {

                this.environmentGroup = new THREE.Group();

                this.scene.add(this.environmentGroup);

            }

            this.wallSconceLights = [];



            if (this.currentTheme === 'modern') {

                this.buildModernEnvironment(this.environmentGroup);

                if (this.scene) {

                    this.scene.background = new THREE.Color(0xdde3ea);

                    this.scene.fog = new THREE.FogExp2(0xdde3ea, 0.006);

                }

            } else {

                this.buildJapaneseEnvironment(this.environmentGroup);

                if (this.scene) {

                    this.scene.background = new THREE.Color(0xd8cbba);

                    this.scene.fog = new THREE.FogExp2(0xd8cbba, 0.007);

                }

            }



            const themeSelect = document.getElementById('officeThemeSelect');

            if (themeSelect && themeSelect.value !== this.currentTheme) {

                themeSelect.value = this.currentTheme;

            }

        }



        setTheme(themeName) {

            if (themeName !== 'japanese' && themeName !== 'modern') return;

            this.currentTheme = themeName;

            try {

                localStorage.setItem('doraemon_office_theme', themeName);

            } catch (e) {}



            const themeSelect = document.getElementById('officeThemeSelect');

            if (themeSelect) themeSelect.value = themeName;



            if (this.environmentGroup) {

                while (this.environmentGroup.children.length > 0) {

                    const obj = this.environmentGroup.children[0];

                    this.environmentGroup.remove(obj);

                    if (obj.geometry) obj.geometry.dispose();

                    if (obj.material) {

                        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());

                        else obj.material.dispose();

                    }

                }

            }

            this.wallSconceLights = [];



            this.buildCurrentTheme();



            // Rebuild clickableObjects for seamless interaction in newly rendered room

            this.clickableObjects = [];

            if (this.nobita && this.nobita.character) {

                this.nobita.character.traverse((child) => {

                    if (child.isMesh || child.isSprite) this.clickableObjects.push(child);

                });

            }

            for (const c of this.characters) {

                if (c.mesh) {

                    c.mesh.traverse((child) => {

                        if (child.isMesh || child.isSprite) this.clickableObjects.push(child);

                    });

                }

            }

        }



        buildJapaneseEnvironment(envGroup = this.environmentGroup) {

            const targetGroup = envGroup || this.scene;

            const roomW = 34;

            const roomD = 34;

            const CEILING_Y = 10.0;



            // 1. FLOOR: Rich Japanese Walnut

            const floorGeo = new THREE.PlaneGeometry(roomW, roomD);

            const oakTex = createRichWalnutFloorTexture();

            oakTex.repeat.set(5, 5);

            const floor = new THREE.Mesh(floorGeo, new THREE.MeshStandardMaterial({ map: oakTex, roughness: 0.55, metalness: 0.08 }));

            floor.rotation.x = -Math.PI / 2;

            floor.receiveShadow = true;

            targetGroup.add(floor);



            // 2. RAISED TATAMI PAVILION

            const tatamiGeo = new THREE.PlaneGeometry(20, 16);

            const tatamiTex = createTatamiWovenTexture();

            tatamiTex.repeat.set(2.5, 2);

            const tatami = new THREE.Mesh(tatamiGeo, new THREE.MeshStandardMaterial({ map: tatamiTex, roughness: 0.85 }));

            tatami.rotation.x = -Math.PI / 2;

            tatami.position.set(0, 0.06, 0.5);

            tatami.receiveShadow = true;

            targetGroup.add(tatami);



            const curbMat = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.5 });

            const curbT = new THREE.Mesh(new THREE.BoxGeometry(20.4, 0.12, 0.3), curbMat);

            curbT.position.set(0, 0.06, -7.5);

            const curbB = new THREE.Mesh(new THREE.BoxGeometry(20.4, 0.12, 0.3), curbMat);

            curbB.position.set(0, 0.06, 8.5);

            const curbL = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.12, 16.4), curbMat);

            curbL.position.set(-10.2, 0.06, 0.5);

            const curbR = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.12, 16.4), curbMat);

            curbR.position.set(10.2, 0.06, 0.5);

            targetGroup.add(curbT, curbB, curbL, curbR);



            // 3. WALLS

            const wallH = CEILING_Y;

            const wallMat = new THREE.MeshStandardMaterial({ color: 0xd6c7b2, roughness: 0.85 });

            const cedarMat = new THREE.MeshStandardMaterial({ color: 0x5a3418, roughness: 0.55 });



            const backWall = new THREE.Mesh(new THREE.BoxGeometry(roomW, wallH, 0.6), wallMat);

            backWall.position.set(0, wallH / 2, -roomD / 2);

            backWall.receiveShadow = true;

            targetGroup.add(backWall);



            const baseboardB = new THREE.Mesh(new THREE.BoxGeometry(roomW, 0.6, 0.7), cedarMat);

            baseboardB.position.set(0, 0.3, -roomD / 2);

            targetGroup.add(baseboardB);



            const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.6, wallH, roomD), wallMat);

            leftWall.position.set(-roomW / 2, wallH / 2, 0);

            leftWall.receiveShadow = true;

            targetGroup.add(leftWall);



            const baseboardL = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.6, roomD), cedarMat);

            baseboardL.position.set(-roomW / 2, 0.3, 0);

            targetGroup.add(baseboardL);



            // 4. CEDAR WOOD LOUVER ACCENT WALL

            const louverGroup = new THREE.Group();

            for (let i = 0; i < 24; i++) {

                const slat = new THREE.Mesh(new THREE.BoxGeometry(0.2, 8.5, 0.28), cedarMat);

                slat.position.set(-14.5 + i * 0.45, 4.8, -roomD / 2 + 0.42);

                slat.castShadow = true;

                louverGroup.add(slat);

            }

            targetGroup.add(louverGroup);



            // 5. 4-PANEL SHOJI SLIDING SCREEN WALL

            const shojiGeo = new THREE.PlaneGeometry(16, 7.5);

            const shojiTex = createShojiLatticeTexture();

            shojiTex.repeat.set(3.5, 1);

            const shojiWall = new THREE.Mesh(shojiGeo, new THREE.MeshStandardMaterial({ map: shojiTex, roughness: 0.5 }));

            shojiWall.position.set(5.5, 4.8, -roomD / 2 + 0.32);

            targetGroup.add(shojiWall);



            // 6. MOUNT FUJI ARTWORK

            const fujiGeo = new THREE.PlaneGeometry(10.5, 5.2);

            const fujiFrame = new THREE.Mesh(fujiGeo, new THREE.MeshStandardMaterial({ map: createFujiPanoramaTexture() }));

            fujiFrame.position.set(-roomW / 2 + 0.32, 5.5, -4);

            fujiFrame.rotation.y = Math.PI / 2;

            targetGroup.add(fujiFrame);



            // 7. STRATEGY WHITEBOARD

            const wbGeo = new THREE.PlaneGeometry(7.8, 4.0);

            const whiteboard = new THREE.Mesh(wbGeo, new THREE.MeshStandardMaterial({ map: createWhiteboardTexture(), roughness: 0.2 }));

            whiteboard.position.set(-roomW / 2 + 0.32, 5.2, 7.5);

            whiteboard.rotation.y = Math.PI / 2;

            targetGroup.add(whiteboard);



            // 8. EXECUTIVE CONFERENCE ROOM (12-Chair Extended Open Legroom Table)

            this.buildExecutiveMeetingArea(9.5, 0, -8.5, targetGroup, 'japanese');



            // 9. TEA LOUNGE, VENDING BAR & ZEN GARDEN

            this.buildJapaneseTeaSofaLounge(10.5, 0, 8.0, targetGroup);

            this.buildJapaneseVendingBar(-13.0, 0, -12.5, targetGroup);

            this.buildZenGardenCorner(-12.5, 0, 10.5, targetGroup);

            this.buildExecutiveBookshelf(13.8, 0, 0, targetGroup);

            this.buildBackWallSmartTv(targetGroup);



            // 10. WALL LIGHT SWITCH (Left Wall Corner: -16.7, 2.2, -10.0)

            this.buildWallLightSwitch(-16.7, 2.2, -10.0, targetGroup);



            // 11. DECORATIVE WALL SCONCES WITH GENTLE WARM LIGHT (Replaces the 3 ceiling hanging lanterns)

            this.buildDecorativeWallSconces(targetGroup);

        }



        buildWallLightSwitch(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);

            group.rotation.y = Math.PI / 2;



            const plateMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 });

            const plate = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.50, 0.05), plateMat);

            group.add(plate);



            const leverBase = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.16, 0.04), new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.7 }));

            leverBase.position.set(0, 0, 0.03);

            group.add(leverBase);



            const leverMat = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.2, metalness: 0.3 });

            const lever = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.18, 0.08), leverMat);

            lever.position.set(0, 0, 0.07);

            group.add(lever);



            this.lightSwitchLever = lever;

            (parentGroup || this.scene).add(group);

        }



        buildExecutiveMeetingArea(x, y, z, parentGroup = this.environmentGroup, style = 'japanese') {

            const group = new THREE.Group();

            group.position.set(x, y, z);

            const targetGroup = parentGroup || this.scene;



            const isModern = (style === 'modern' || this.currentTheme === 'modern');

            const tableColor = isModern ? 0x241812 : 0x4a2a12;

            const colColor = isModern ? 0x334155 : 0x271911;



            // 10.8m x 2.5m Table Top

            const woodMat = new THREE.MeshStandardMaterial({

                color: tableColor,

                roughness: isModern ? 0.35 : 0.40,

                metalness: isModern ? 0.15 : 0.10

            });

            const topGeo = createRoundedBoxGeometry(10.8, 0.10, 2.5, 0.40, 5);

            const tableTop = new THREE.Mesh(topGeo, woodMat);

            tableTop.position.y = 0.75;

            tableTop.castShadow = true;

            group.add(tableTop);



            // Modern connectivity hatch

            if (isModern) {

                const centerStrip = new THREE.Mesh(

                    new THREE.BoxGeometry(5.6, 0.015, 0.26),

                    new THREE.MeshStandardMaterial({ color: 0x18181b, metalness: 0.85, roughness: 0.3 })

                );

                centerStrip.position.set(0, 0.81, 0);

                group.add(centerStrip);

            }



            // 3 Pedestal Bases (x = -3.4, 0, 3.4)

            const colMat = new THREE.MeshStandardMaterial({

                color: colColor,

                metalness: isModern ? 0.80 : 0.40,

                roughness: isModern ? 0.25 : 0.50

            });

            for (let cx of [-3.4, 0, 3.4]) {

                const col = new THREE.Mesh(new THREE.CylinderGeometry(0.40, 0.45, 0.70, 16), colMat);

                col.position.set(cx, 0.35, 0);

                col.castShadow = true;

                group.add(col);

            }



            // 2 Conference phones

            for (let px of [-2.0, 2.0]) {

                const phone = new THREE.Mesh(new THREE.CylinderGeometry(0.20, 0.28, 0.08, 8), new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 }));

                phone.position.set(px, 0.84, 0);

                group.add(phone);

            }



            // CEO Head Chair at x = -4.75

            const headChair = buildExecutiveLeatherChair();

            headChair.position.set(-4.75, 0, 0);

            headChair.rotation.y = Math.PI / 2;

            group.add(headChair);



            // 12 Conference Chairs

            const chairColor = isModern ? 0x1e293b : 0x1f2937;

            for (let side of [-1, 1]) {

                for (let c = 0; c < 6; c++) {

                    const chair = buildStandardOfficeChair(chairColor);

                    chair.position.set(-3.75 + c * 1.50, 0, side * 1.55);

                    chair.rotation.y = side === 1 ? Math.PI : 0;

                    group.add(chair);

                }

            }



            // Modern linear overhead architectural pendant suspended above table

            if (isModern) {

                const pendantMat = new THREE.MeshStandardMaterial({ color: 0x18181b, metalness: 0.9, roughness: 0.2 });

                const pendantBar = new THREE.Mesh(new THREE.BoxGeometry(8.8, 0.08, 0.18), pendantMat);

                pendantBar.position.set(0, 5.8, 0);

                const ledStrip = new THREE.Mesh(

                    new THREE.BoxGeometry(8.6, 0.02, 0.12),

                    new THREE.MeshStandardMaterial({ color: 0xffedd5, emissive: 0xfef08a, emissiveIntensity: 0.85, roughness: 0.2 })

                );

                ledStrip.position.set(0, 5.75, 0);

                group.add(pendantBar, ledStrip);



                // Suspension cables from ceiling

                const wireMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.2 });

                for (let wx of [-3.5, 3.5]) {

                    const wire = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 4.2), wireMat);

                    wire.position.set(wx, 7.9, 0);

                    group.add(wire);

                }

            }



            targetGroup.add(group);

        }



        buildJapaneseTeaSofaLounge(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);



            const sofaMat = new THREE.MeshStandardMaterial({ color: 0x374151, roughness: 0.8 });

            const sofaSeat = new THREE.Mesh(createRoundedBoxGeometry(5.2, 0.5, 1.8, 0.15, 3), sofaMat);

            sofaSeat.position.set(0, 0.35, 0);

            const sofaBack = new THREE.Mesh(createRoundedBoxGeometry(5.2, 1.0, 0.4, 0.15, 3), sofaMat);

            sofaBack.position.set(0, 0.95, 0.85);



            const tableMat = new THREE.MeshStandardMaterial({ color: 0x4a2a12, roughness: 0.5 });

            const teaTable = new THREE.Mesh(createRoundedBoxGeometry(3.2, 0.45, 1.2, 0.1, 2), tableMat);

            teaTable.position.set(0, 0.25, -1.6);



            for (let i = -1; i <= 1; i += 2) {

                const teaCup = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.08, 0.15, 12), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2 }));

                teaCup.position.set(i * 0.7, 0.55, -1.6);

                group.add(teaCup);

            }



            group.add(sofaSeat, sofaBack, teaTable);

            (parentGroup || this.scene).add(group);

        }



        buildJapaneseVendingBar(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);



            const vendMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.3, metalness: 0.3 });

            const vendBody = new THREE.Mesh(createRoundedBoxGeometry(2.0, 4.2, 1.4, 0.1, 2), vendMat);

            vendBody.position.set(0, 2.1, 0);



            const screen = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 2.2), new THREE.MeshBasicMaterial({ color: 0xffffff }));

            screen.position.set(0, 2.4, 0.71);



            const counterMat = new THREE.MeshStandardMaterial({ color: 0x292524, roughness: 0.6 });

            const coffeeCounter = new THREE.Mesh(createRoundedBoxGeometry(3.5, 1.8, 1.4, 0.08, 2), counterMat);

            coffeeCounter.position.set(3.2, 0.9, 0);



            const coffeeMachine = new THREE.Mesh(createRoundedBoxGeometry(1.2, 1.2, 1.0, 0.05, 2), new THREE.MeshStandardMaterial({ color: 0xdc2626, metalness: 0.6 }));

            coffeeMachine.position.set(3.2, 2.4, 0);



            group.add(vendBody, screen, coffeeCounter, coffeeMachine);

            (parentGroup || this.scene).add(group);

        }



        buildZenGardenCorner(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);



            const sandMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.95 });

            const sandBed = new THREE.Mesh(new THREE.BoxGeometry(5.0, 0.15, 5.0), sandMat);

            sandBed.position.set(0, 0.08, 0);



            const stoneBorderMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 });

            const borderT = new THREE.Mesh(new THREE.BoxGeometry(5.4, 0.35, 0.2), stoneBorderMat);

            borderT.position.set(0, 0.18, -2.5);

            const borderB = new THREE.Mesh(new THREE.BoxGeometry(5.4, 0.35, 0.2), stoneBorderMat);

            borderB.position.set(0, 0.18, 2.5);

            const borderL = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.35, 5.4), stoneBorderMat);

            borderL.position.set(-2.5, 0.18, 0);

            const borderR = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.35, 5.4), stoneBorderMat);

            borderR.position.set(2.5, 0.18, 0);



            const rockMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.9 });

            const rock1 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.85), rockMat);

            rock1.position.set(-0.8, 0.65, -0.6);

            const rock2 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.55), rockMat);

            rock2.position.set(0.9, 0.45, 0.8);



            const potMat = new THREE.MeshStandardMaterial({ color: 0x1f2937, roughness: 0.6 });

            const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.35, 0.7, 16), potMat);

            pot.position.set(0.2, 0.45, -0.2);



            const foliageMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.7 });

            const bonsaiFoliage = new THREE.Mesh(new THREE.SphereGeometry(0.95, 12, 12), foliageMat);

            bonsaiFoliage.position.set(0.2, 1.4, -0.2);

            bonsaiFoliage.scale.set(1.4, 0.7, 1.2);



            group.add(sandBed, borderT, borderB, borderL, borderR, rock1, rock2, pot, bonsaiFoliage);

            (parentGroup || this.scene).add(group);

        }





        // =========================================================================

        // EXECUTIVE SMART TV ON BACK WALL BEHIND CIO (Yêu cầu mới: Chuyển vị trí chiếu YouTube qua bức tường phía sau CIO)

        // =========================================================================

        buildBackWallSmartTv(parentGroup = this.environmentGroup) {

            const tvGroup = new THREE.Group();

            tvGroup.name = 'tvGroup';

            // Vị trí: Ngay chính giữa bức tường phía sau CIO (x = 0, y = 5.2, z = -16.35)

            // Bức tường sau ở z = -17.0, rèm cửa loft / nan gỗ ở z = -16.60

            // Chiều cao màn hình 7.1m (từ y = 1.65m đến 8.75m), chiều rộng 12.6m (từ x = -6.3m đến +6.3m)

            // Mặt màn hình hướng về phía trước căn phòng (+Z), nhìn thẳng vào phòng làm việc và người xem

            tvGroup.position.set(0, 5.2, -16.35);



            const tvFrameMat = new THREE.MeshStandardMaterial({

                color: 0x0f172a,

                metalness: 0.85,

                roughness: 0.2

            });

            const tvFrame = new THREE.Mesh(new THREE.BoxGeometry(12.8, 7.3, 0.14), tvFrameMat);



            const tvScreenMat = new THREE.MeshStandardMaterial({

                map: createTvStandbyTexture(),

                roughness: 0.2,

                metalness: 0.1

            });

            const tvScreen = new THREE.Mesh(new THREE.PlaneGeometry(12.6, 7.1), tvScreenMat);

            tvScreen.position.set(0, 0, 0.08); // Hướng mặt về phía trước căn phòng (+Z)

            tvGroup.add(tvFrame, tvScreen);



            tvGroup.visible = !!this.isVideoPlaying;

            (parentGroup || this.scene).add(tvGroup);

            this.tvGroup = tvGroup;

            this.tvScreenMesh = tvScreen;

        }



        buildExecutiveBookshelf(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);

            group.rotation.y = -Math.PI / 2;



            const woodMat = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.5 });

            const shelfFrame = new THREE.Mesh(createRoundedBoxGeometry(10.0, 7.5, 1.2, 0.08, 2), woodMat);

            shelfFrame.position.set(0, 3.75, 0);

            group.add(shelfFrame);



            const colors = [0x991b1b, 0x1e3a8a, 0x065f46, 0x854d0e, 0x374151];

            for (let row = 0; row < 4; row++) {

                const shelfY = 1.2 + row * 1.6;

                for (let col = -4; col <= 4; col += 1.8) {

                    const book = new THREE.Mesh(

                        new THREE.BoxGeometry(0.28, 0.95, 0.75),

                        new THREE.MeshStandardMaterial({ color: colors[Math.abs(row * 3 + col) % colors.length] })

                    );

                    book.position.set(col + (Math.random() - 0.5) * 0.2, shelfY + 0.48, 0.05);

                    book.rotation.z = (Math.random() - 0.5) * 0.15;

                    group.add(book);

                }

            }



// (Smart TV da duoc chuyen sang buc tuong phia sau CIO - buildBackWallSmartTv)



            (parentGroup || this.scene).add(group);

        }



        // =========================================================================

        // DECORATIVE WALL SCONCES WITH GENTLE WARM LIGHT (Yêu cầu 1)

        // =========================================================================

        buildWallSconce(x, y, z, rotY = 0) {

            const sconceGroup = new THREE.Group();

            sconceGroup.position.set(x, y, z);

            sconceGroup.rotation.y = rotY;



            // Architectural mounting plate

            const plateMat = new THREE.MeshStandardMaterial({ color: 0x18181b, metalness: 0.85, roughness: 0.3 });

            const plate = new THREE.Mesh(new THREE.BoxGeometry(0.20, 0.60, 0.04), plateMat);

            sconceGroup.add(plate);



            // Warm brass / bronze cylinder fixture body

            const bodyMat = new THREE.MeshStandardMaterial({ color: 0xbf9b60, metalness: 0.85, roughness: 0.25 });

            const body = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.40, 16), bodyMat);

            body.position.set(0, 0, 0.10);

            sconceGroup.add(body);



            // Dual top & bottom frosted diffusers with soft warm glow

            const diffuserMat = new THREE.MeshStandardMaterial({

                color: 0xffedd5,

                emissive: 0xfef08a,

                emissiveIntensity: 0.85,

                roughness: 0.15

            });

            const topDiffuser = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.12, 16), diffuserMat);

            topDiffuser.position.set(0, 0.26, 0.10);

            const bottomDiffuser = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.12, 16), diffuserMat);

            bottomDiffuser.position.set(0, -0.26, 0.10);

            sconceGroup.add(topDiffuser, bottomDiffuser);



            // Soft warm point light illuminating wall

            const light = new THREE.PointLight(0xffecd2, 0.42, 6.5, 2);

            light.position.set(0, 0, 0.22);

            sconceGroup.add(light);

            if (!this.wallSconceLights) this.wallSconceLights = [];

            this.wallSconceLights.push(light);



            return sconceGroup;

        }



        buildDecorativeWallSconces(parentGroup = this.environmentGroup) {

            const target = parentGroup || this.scene;

            if (!this.wallSconceLights) this.wallSconceLights = [];



            // Back wall sconces (y = 4.2, z = -16.65, rotY = 0)

            for (let bx of [-11.5, -4.5, 4.5, 11.5]) {

                target.add(this.buildWallSconce(bx, 4.2, -16.65, 0));

            }



            // Left wall sconces (x = -16.65, y = 4.2, rotY = Math.PI / 2)

            for (let lz of [-9.0, 0.5, 9.0]) {

                target.add(this.buildWallSconce(-16.65, 4.2, lz, Math.PI / 2));

            }



            // Right wall sconces (x = 16.65, y = 4.2, rotY = -Math.PI / 2)

            for (let rz of [-8.0, 8.0]) {

                target.add(this.buildWallSconce(16.65, 4.2, rz, -Math.PI / 2));

            }

        }



        // =========================================================================

        // KIỂU 2: PHONG CÁCH HIỆN ĐẠI (MODERN EXECUTIVE STUDIO - Yêu cầu 2)

        // =========================================================================

        buildModernEnvironment(envGroup = this.environmentGroup) {

            const roomW = 34;

            const roomD = 34;

            const CEILING_Y = 10.0;

            const targetGroup = envGroup || this.scene;



            // 1. BASE FLOOR: Glossy Grey Tiled Porcelain Floor (Yêu cầu 1)

            const floorGeo = new THREE.PlaneGeometry(roomW, roomD);

            const floorTex = createGlossyTileFloorTexture();

            floorTex.repeat.set(16, 16);

            const floorMat = new THREE.MeshStandardMaterial({

                map: floorTex,

                color: 0x64748b,

                roughness: 0.38,

                metalness: 0.08

            });

            const floor = new THREE.Mesh(floorGeo, floorMat);

            floor.rotation.x = -Math.PI / 2;

            floor.receiveShadow = true;

            targetGroup.add(floor);



            // 2. CENTRAL EXECUTIVE ZONE: Glossy Grey Tiled Floor with Glowing LED Contour (Yêu cầu 1)

            const rugGeo = new THREE.BoxGeometry(22, 0.04, 17);

            const centralTileTex = createGlossyTileFloorTexture();

            centralTileTex.repeat.set(11, 8.5);

            const rugMat = new THREE.MeshStandardMaterial({

                map: centralTileTex,

                color: 0x6e7889,

                roughness: 0.36,

                metalness: 0.08

            });

            const rug = new THREE.Mesh(rugGeo, rugMat);

            rug.position.set(0, 0.02, 0.5);

            rug.receiveShadow = true;

            targetGroup.add(rug);



            // Glowing LED edge perimeter border

            const ledMat = new THREE.MeshStandardMaterial({

                color: 0xfef08a,

                emissive: 0xfef08a,

                emissiveIntensity: 0.75,

                roughness: 0.2

            });

            const ledT = new THREE.Mesh(new THREE.BoxGeometry(22.2, 0.03, 0.08), ledMat);

            ledT.position.set(0, 0.03, -8.0);

            const ledB = new THREE.Mesh(new THREE.BoxGeometry(22.2, 0.03, 0.08), ledMat);

            ledB.position.set(0, 0.03, 9.0);

            const ledL = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.03, 17.0), ledMat);

            ledL.position.set(-11.0, 0.03, 0.5);

            const ledR = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.03, 17.0), ledMat);

            ledR.position.set(11.0, 0.03, 0.5);

            targetGroup.add(ledT, ledB, ledL, ledR);



            // 3. WALLS & FLUTED WOOD ACOUSTIC PANELS

            const wallMat = new THREE.MeshStandardMaterial({ color: 0x272422, roughness: 0.8 });

            const flutedTex = createFlutedWoodTexture();

            flutedTex.repeat.set(8, 1);

            const flutedMat = new THREE.MeshStandardMaterial({ map: flutedTex, roughness: 0.55 });



            // Back wall base structure

            const backWall = new THREE.Mesh(new THREE.BoxGeometry(roomW, CEILING_Y, 0.6), wallMat);

            backWall.position.set(0, CEILING_Y / 2, -roomD / 2);

            targetGroup.add(backWall);



            // Fluted piers on left & right of back wall

            const pierL = new THREE.Mesh(new THREE.BoxGeometry(4.5, CEILING_Y, 0.4), flutedMat);

            pierL.position.set(-14.5, CEILING_Y / 2, -roomD / 2 + 0.35);

            const pierR = new THREE.Mesh(new THREE.BoxGeometry(4.5, CEILING_Y, 0.4), flutedMat);

            pierR.position.set(14.5, CEILING_Y / 2, -roomD / 2 + 0.35);

            targetGroup.add(pierL, pierR);



            // 4. PANORAMIC DOUBLE-HEIGHT LOFT WINDOWS WITH VENETIAN BLINDS & OUTDOOR VIEW

            const outdoorGeo = new THREE.PlaneGeometry(25, 8.2);

            const blindsTex = createVenetianBlindsTexture();

            blindsTex.repeat.set(2, 1);

            const windowMat = new THREE.MeshStandardMaterial({

                map: blindsTex,

                roughness: 0.3,

                metalness: 0.05,

                emissive: 0xffffff,

                emissiveMap: blindsTex,

                emissiveIntensity: 0.42

            });

            const blindsMesh = new THREE.Mesh(outdoorGeo, windowMat);

            blindsMesh.position.set(0, 5.0, -roomD / 2 + 0.32);

            targetGroup.add(blindsMesh);



            // Sleek black architectural aluminum window frames & mullions

            const frameMat = new THREE.MeshStandardMaterial({ color: 0x18181b, metalness: 0.85, roughness: 0.25 });

            const winTop = new THREE.Mesh(new THREE.BoxGeometry(24.5, 0.16, 0.25), frameMat);

            winTop.position.set(0, 8.8, -roomD / 2 + 0.4);

            const winBottom = new THREE.Mesh(new THREE.BoxGeometry(24.5, 0.20, 0.35), frameMat);

            winBottom.position.set(0, 1.2, -roomD / 2 + 0.4);

            targetGroup.add(winTop, winBottom);



            for (let mx of [-12.2, -6.1, 0, 6.1, 12.2]) {

                const mul = new THREE.Mesh(new THREE.BoxGeometry(0.18, 7.6, 0.22), frameMat);

                mul.position.set(mx, 5.0, -roomD / 2 + 0.4);

                targetGroup.add(mul);

            }

            const winTransom = new THREE.Mesh(new THREE.BoxGeometry(24.5, 0.12, 0.20), frameMat);

            winTransom.position.set(0, 5.2, -roomD / 2 + 0.4);

            targetGroup.add(winTransom);



            // Fluted wood sill below window

            const sillMat = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.5 });

            const sill = new THREE.Mesh(new THREE.BoxGeometry(24.5, 1.2, 0.4), sillMat);

            sill.position.set(0, 0.6, -roomD / 2 + 0.35);

            targetGroup.add(sill);



            // 5. LEFT WALL: Acoustic Fluted Wood Slat Paneling

            const leftWallGeo = new THREE.BoxGeometry(0.6, CEILING_Y, roomD);

            const leftWall = new THREE.Mesh(leftWallGeo, wallMat);

            leftWall.position.set(-roomW / 2, CEILING_Y / 2, 0);

            targetGroup.add(leftWall);



            const leftFluted = new THREE.Mesh(new THREE.PlaneGeometry(roomD, CEILING_Y), flutedMat);

            leftFluted.rotation.y = Math.PI / 2;

            leftFluted.position.set(-roomW / 2 + 0.32, CEILING_Y / 2, 0);

            targetGroup.add(leftFluted);



            // Modern Framed Art on Left Wall

            const artGeo = new THREE.PlaneGeometry(9.0, 4.8);

            const artMesh = new THREE.Mesh(artGeo, new THREE.MeshStandardMaterial({ map: createFujiPanoramaTexture(), roughness: 0.4 }));

            artMesh.rotation.y = Math.PI / 2;

            artMesh.position.set(-roomW / 2 + 0.42, 5.5, -4.5);

            const artFrame = new THREE.Mesh(new THREE.BoxGeometry(0.08, 5.0, 9.2), frameMat);

            artFrame.position.set(-roomW / 2 + 0.36, 5.5, -4.5);

            targetGroup.add(artMesh, artFrame);



            // Strategy Glass Mindmap Wall on Left Wall

            const glassGeo = new THREE.PlaneGeometry(8.5, 4.4);

            const glassTex = createGlassMindmapTexture();

            const glassMat = new THREE.MeshStandardMaterial({

                map: glassTex,

                roughness: 0.15,

                metalness: 0.1,

                transparent: true,

                opacity: 0.95

            });

            const glassMindmap = new THREE.Mesh(glassGeo, glassMat);

            glassMindmap.rotation.y = Math.PI / 2;

            glassMindmap.position.set(-roomW / 2 + 0.40, 5.2, 7.5);

            const glassBacking = new THREE.Mesh(new THREE.BoxGeometry(0.04, 4.5, 8.6), new THREE.MeshStandardMaterial({

                color: 0xffffff,

                roughness: 0.3

            }));

            glassBacking.position.set(-roomW / 2 + 0.37, 5.2, 7.5);

            targetGroup.add(glassMindmap, glassBacking);



            // 6. RIGHT WALL: Tall Dark Walnut Display Cabinet & Bookshelves

            this.buildModernExecutiveBookshelf(16.2, 0, 0, targetGroup);

            this.buildBackWallSmartTv(targetGroup);



            // 7. CEILING & BLACK ARCHITECTURAL LIGHTING TRACKS

            this.buildModernCeilingTracks(CEILING_Y, targetGroup);



            // 8. MODERN LOUNGE (Circular Rug + Round Marble Table + Charcoal L-Sofa)

            this.buildModernLounge(10.5, 0, 7.5, targetGroup);



            // 9. MODERN POTTED PLANTS (Fiddle Leaf Fig trees in white ceramic cylinders)

            this.buildModernPottedPlant(-14.6, 0, -11.5, 1.15, targetGroup);

            this.buildModernPottedPlant(14.0, 0, 5.5, 1.1, targetGroup);



            // 10. EXECUTIVE CONFERENCE AREA (Sleek Modern 12-Chair Table + Suspension Pendant)

            this.buildExecutiveMeetingArea(9.5, 0, -8.5, targetGroup, 'modern');



            // 11. DECORATIVE WALL SCONCES (Warm, gentle accent glow along walls)

            this.buildDecorativeWallSconces(targetGroup);



            // 12. WALL LIGHT SWITCH

            this.buildWallLightSwitch(-16.7, 2.2, -10.0, targetGroup);

        }



        buildModernExecutiveBookshelf(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);

            group.rotation.y = -Math.PI / 2;



            const woodMat = new THREE.MeshStandardMaterial({ color: 0x221711, roughness: 0.45 });

            const shelfFrame = new THREE.Mesh(createRoundedBoxGeometry(16.0, 8.5, 1.2, 0.1, 2), woodMat);

            shelfFrame.position.set(0, 4.25, 0);

            group.add(shelfFrame);



            // Recessed warm LED backlit display niches

            const colors = [0x991b1b, 0x1e3a8a, 0x0f766e, 0x854d0e, 0x334155, 0x475569];

            for (let row = 0; row < 4; row++) {

                const shelfY = 1.4 + row * 1.8;

                // Warm LED strip under shelf

                const ledStrip = new THREE.Mesh(

                    new THREE.BoxGeometry(15.6, 0.02, 0.08),

                    new THREE.MeshStandardMaterial({ color: 0xffedd5, emissive: 0xfef08a, emissiveIntensity: 0.65, roughness: 0.2 })

                );

                ledStrip.position.set(0, shelfY + 1.7, 0.4);

                group.add(ledStrip);



                for (let col = -7; col <= 7; col += 1.6) {

                    if (Math.abs(col) < 1.2 && row === 1) continue; // Bar display niche

                    const book = new THREE.Mesh(

                        new THREE.BoxGeometry(0.32, 1.15, 0.85),

                        new THREE.MeshStandardMaterial({ color: colors[Math.abs(row * 4 + col) % colors.length] })

                    );

                    book.position.set(col + (Math.random() - 0.5) * 0.15, shelfY + 0.58, 0.1);

                    book.rotation.z = (Math.random() - 0.5) * 0.12;

                    group.add(book);

                }

            }



// (Smart TV da duoc chuyen sang buc tuong phia sau CIO - buildBackWallSmartTv)



            (parentGroup || this.scene).add(group);

        }



        buildModernCeilingTracks(ceilingY, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            const trackMat = new THREE.MeshStandardMaterial({ color: 0x18181b, metalness: 0.85, roughness: 0.3 });

            const spotBodyMat = new THREE.MeshStandardMaterial({ color: 0x27272a, metalness: 0.8, roughness: 0.3 });

            const spotLensMat = new THREE.MeshStandardMaterial({

                color: 0xffedd5,

                emissive: 0xfef08a,

                emissiveIntensity: 0.85,

                roughness: 0.15

            });



            // 2 Longitudinal Black Track Rails

            for (let tx of [-5.5, 5.5]) {

                const rail = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.06, 26.0), trackMat);

                rail.position.set(tx, ceilingY - 0.08, 0);

                group.add(rail);



                // Spotlights along rail

                for (let sz of [-10, -5, 0, 5, 10]) {

                    const spot = new THREE.Group();

                    spot.position.set(tx, ceilingY - 0.15, sz);

                    const head = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.24, 12), spotBodyMat);

                    head.rotation.x = 0.25;

                    const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.02, 12), spotLensMat);

                    lens.position.y = -0.12;

                    lens.rotation.x = 0.25;

                    spot.add(head, lens);

                    group.add(spot);

                }

            }



            // 1 Transversal Rail

            const crossRail = new THREE.Mesh(new THREE.BoxGeometry(22.0, 0.06, 0.08), trackMat);

            crossRail.position.set(0, ceilingY - 0.08, -4.0);

            group.add(crossRail);



            (parentGroup || this.scene).add(group);

        }



        buildModernLounge(x, y, z, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);



            // 1. Circular Lounge Rug (Radius 2.4m)

            const rugMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.95 });

            const circRug = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 0.04, 32), rugMat);

            circRug.position.y = 0.02;

            group.add(circRug);



            // 2. Round White Marble Coffee Table (Radius 0.95m, Surface at y = 0.44m)

            const marbleMat = new THREE.MeshStandardMaterial({

                map: createMarbleTexture(),

                roughness: 0.18,

                metalness: 0.15

            });

            const marbleTop = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 0.95, 0.06, 32), marbleMat);

            marbleTop.position.y = 0.44;

            marbleTop.castShadow = true;

            group.add(marbleTop);



            // Tripod black metal tapered legs

            const legMat = new THREE.MeshStandardMaterial({ color: 0x18181b, metalness: 0.9, roughness: 0.2 });

            for (let a = 0; a < 3; a++) {

                const angle = a * (Math.PI * 2 / 3);

                const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.015, 0.42, 8), legMat);

                leg.position.set(Math.cos(angle) * 0.65, 0.21, Math.sin(angle) * 0.65);

                leg.rotation.z = Math.cos(angle) * 0.12;

                leg.rotation.x = Math.sin(angle) * 0.12;

                group.add(leg);

            }



            // Tabletop decor: architecture book & succulent

            const book = new THREE.Mesh(createRoundedBoxGeometry(0.40, 0.04, 0.30, 0.02, 2), new THREE.MeshStandardMaterial({ color: 0x0f172a }));

            book.position.set(0.15, 0.49, 0.1);

            const plantPot = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.06, 0.12, 12), new THREE.MeshStandardMaterial({ color: 0xf8fafc }));

            plantPot.position.set(-0.25, 0.53, -0.15);

            group.add(book, plantPot);



            // 3. Contemporary L-shaped Charcoal Lounge Sofa

            const sofaMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.85 });

            // Main sofa body & backrest

            const mainSeat = new THREE.Mesh(createRoundedBoxGeometry(3.6, 0.45, 1.1, 0.12, 3), sofaMat);

            mainSeat.position.set(-0.2, 0.28, 1.35);

            const mainBack = new THREE.Mesh(createRoundedBoxGeometry(3.6, 0.55, 0.35, 0.10, 3), sofaMat);

            mainBack.position.set(-0.2, 0.70, 1.75);



            // Return chaise lounge

            const chaiseSeat = new THREE.Mesh(createRoundedBoxGeometry(1.1, 0.45, 2.2, 0.12, 3), sofaMat);

            chaiseSeat.position.set(1.45, 0.28, 0.10);

            const chaiseBack = new THREE.Mesh(createRoundedBoxGeometry(0.35, 0.55, 2.2, 0.10, 3), sofaMat);

            chaiseBack.position.set(1.85, 0.70, 0.10);

            group.add(mainSeat, mainBack, chaiseSeat, chaiseBack);



            // Designer accent cushions (Mustard ochre & Light greige)

            const cMat1 = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.7 });

            const cMat2 = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.7 });

            const cMat3 = new THREE.MeshStandardMaterial({ color: 0x0d9488, roughness: 0.7 });

            const c1 = new THREE.Mesh(createRoundedBoxGeometry(0.48, 0.48, 0.18, 0.08, 2), cMat1);

            c1.position.set(-1.2, 0.65, 1.55);

            c1.rotation.y = 0.2;

            const c2 = new THREE.Mesh(createRoundedBoxGeometry(0.48, 0.48, 0.18, 0.08, 2), cMat2);

            c2.position.set(0.4, 0.65, 1.55);

            c2.rotation.y = -0.15;

            const c3 = new THREE.Mesh(createRoundedBoxGeometry(0.48, 0.48, 0.18, 0.08, 2), cMat3);

            c3.position.set(1.55, 0.65, -0.4);

            c3.rotation.y = Math.PI / 2 + 0.1;

            group.add(c1, c2, c3);



            (parentGroup || this.scene).add(group);

        }



        buildModernPottedPlant(x, y, z, scale = 1.0, parentGroup = this.environmentGroup) {

            const group = new THREE.Group();

            group.position.set(x, y, z);



            // Matte white ceramic cylinder pot

            const potMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.25 });

            const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.42 * scale, 0.36 * scale, 0.88 * scale, 24), potMat);

            pot.position.y = 0.44 * scale;

            pot.castShadow = true;

            group.add(pot);



            // Soil disc

            const soilMat = new THREE.MeshStandardMaterial({ color: 0x271911, roughness: 0.95 });

            const soil = new THREE.Mesh(new THREE.CylinderGeometry(0.39 * scale, 0.39 * scale, 0.08 * scale, 16), soilMat);

            soil.position.y = 0.84 * scale;

            group.add(soil);



            // Fiddle leaf fig trunk

            const trunkMat = new THREE.MeshStandardMaterial({ color: 0x4a2e1b, roughness: 0.8 });

            const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.04 * scale, 0.06 * scale, 1.8 * scale, 8), trunkMat);

            trunk.position.set(0, 1.6 * scale, 0);

            trunk.rotation.z = 0.05;

            group.add(trunk);



            // Broad violin green leaves

            const leafMat = new THREE.MeshStandardMaterial({

                color: 0x15803d,

                roughness: 0.5,

                side: THREE.DoubleSide

            });

            for (let i = 0; i < 14; i++) {

                const angle = i * 0.85;

                const ly = 1.2 * scale + i * 0.15 * scale;

                const leaf = new THREE.Mesh(new THREE.PlaneGeometry(0.42 * scale, 0.65 * scale), leafMat);

                leaf.position.set(Math.cos(angle) * 0.35 * scale, ly, Math.sin(angle) * 0.35 * scale);

                leaf.rotation.y = angle;

                leaf.rotation.x = 0.4 + (i % 3) * 0.15;

                leaf.castShadow = true;

                group.add(leaf);

            }



            (parentGroup || this.scene).add(group);

        }



        // 9. CEO NOBITA: REALISTIC DESK WITH HOLLOW KNEEWELL, ARMS FORWARD

        // =========================================================================

        buildNobitaExecutiveZone() {

            const group = new THREE.Group();

            group.position.set(0, 0, -2.5);



            const deskMat = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.4, metalness: 0.1 });



            // 1. Sleek Desktop (Thickness 12cm, Surface at y = 0.82m)

            const topGeo = createRoundedBoxGeometry(5.4, 0.12, 1.8, 0.22, 4);

            const deskTop = new THREE.Mesh(topGeo, deskMat);

            deskTop.position.set(0, 0.76, 0);

            deskTop.castShadow = true;

            group.add(deskTop);



            // 2. Left & Right Executive Pedestal Cabinets (Legroom in the middle is completely hollow!)

            const pedL = new THREE.Mesh(createRoundedBoxGeometry(1.1, 0.70, 1.5, 0.10, 3), deskMat);

            pedL.position.set(-1.95, 0.35, 0);

            const pedR = new THREE.Mesh(createRoundedBoxGeometry(1.1, 0.70, 1.5, 0.10, 3), deskMat);

            pedR.position.set(1.95, 0.35, 0);

            group.add(pedL, pedR);



            // 3. iPad on Stand (Resting at y = 0.83 on desktop, angled toward CEO)

            const ipadStand = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.08, 0.25), new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 }));

            ipadStand.position.set(0, 0.86, -0.20);

            const ipadBody = new THREE.Mesh(createRoundedBoxGeometry(0.85, 0.02, 1.10, 0.04, 2), new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 }));

            ipadBody.position.set(0, 0.94, -0.20);

            ipadBody.rotation.x = -0.32;

            const ipadScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.80, 1.02), new THREE.MeshBasicMaterial({ color: 0x0284c7 }));

            ipadScreen.position.set(0, 0.96, -0.20);

            ipadScreen.rotation.x = -Math.PI / 2 - 0.32;

            group.add(ipadStand, ipadBody, ipadScreen);



            // 4. Stacks of Document Dossiers

            const fColors = [0x991b1b, 0x1e3a8a, 0x854d0e];

            for (let i = 0; i < 3; i++) {

                const folder = new THREE.Mesh(createRoundedBoxGeometry(0.85, 0.05, 1.15, 0.03, 2), new THREE.MeshStandardMaterial({ color: fColors[i] }));

                folder.position.set(-1.35, 0.85 + i * 0.055, -0.15 + (i % 2) * 0.05);

                folder.rotation.y = (i - 1) * 0.08;

                group.add(folder);

            }



            // Coffee Mug

            const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.08, 0.20, 12), new THREE.MeshStandardMaterial({ color: 0x004b93 }));

            mug.position.set(1.25, 0.92, -0.25);

            group.add(mug);



            // 5. Executive Leather Chair - Pulled naturally behind desk (desk at z = -2.5, chair at z = -3.75)

            const execChair = buildExecutiveLeatherChair();

            execChair.position.set(0, 0, -1.25);

            group.add(execChair);



            // 6. CEO Bắc Nguyễn Model - Directly in World Space at (0, 0.12, -3.75)

            const nobitaModel = this.buildNobitaModel();

            nobitaModel.position.set(0, 0.12, -3.75);



            // 7. FLOATING BILLBOARD BADGE: Attached directly to nobitaModel at y = 3.95 (follows him everywhere)

            const ceoBadge = createFloatingNameBadge('CIO BẮC NGUYỄN', '', true);

            ceoBadge.position.set(0, 3.95, 0);

            nobitaModel.add(ceoBadge);



            nobitaModel.traverse((child) => {

                if (child.isMesh || child.isSprite) {

                    child.userData = {

                        isAssistant: true,

                        isCIO: true,

                        assistantId: 'cio_nobita',

                        assistantName: 'CIO BẮC NGUYỄN',

                        role: 'Giám đốc Điều hành & Chỉ huy Chiến lược AI',

                        charData: {

                            name: 'CIO BẮC NGUYỄN',

                            badge: 'Tổng Giám Đốc',

                            avatar: '👑',

                            color: 0x004b93

                        },

                        asst: {

                            id: 'cio_nobita',

                            name: 'CIO BẮC NGUYỄN',

                            description: 'Tổng Giám đốc Điều hành & Chỉ huy Chiến lược Trợ lý chuyên môn toàn hệ thống HB MIND.',

                            model: 'Gemini 3.5 Pro'

                        }

                    };

                    this.clickableObjects.push(child);

                }

            });

            this.scene.add(nobitaModel);



            this.nobita = {

                group: group,

                character: nobitaModel,

                badge: ceoBadge,

                badgeSprite: ceoBadge,

                chair: execChair,

                homePos: new THREE.Vector3(0, 0.12, -3.75),

                homeRot: 0,

                state: 'working',

                stateTime: 0,

                leftArm: nobitaModel.getObjectByName('leftArm'),

                rightArm: nobitaModel.getObjectByName('rightArm'),

                head: nobitaModel.getObjectByName('head'),

                leftLeg: nobitaModel.getObjectByName('leftLeg'),

                rightLeg: nobitaModel.getObjectByName('rightLeg'),

                walkWaypoints: [],

                isSitting: true

            };



            this.scene.add(group);

        }



        buildNobitaModel() {

            const char = new THREE.Group();

            char.name = 'nobitaRoot';

            const skinMat = new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.7 });

            const suitMat = new THREE.MeshStandardMaterial({ color: 0x181a20, roughness: 0.5 });

            const whiteShirtMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });

            const tieMat = new THREE.MeshStandardMaterial({ color: 0x004b93, roughness: 0.4 });

            const shoeMat = new THREE.MeshStandardMaterial({ color: 0x09090b, roughness: 0.3, metalness: 0.4 });



            // Torso (Tailored Black Suit Jacket)

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.44, 0.95, 14), suitMat);

            torso.position.y = 1.05;

            torso.castShadow = true;

            char.add(torso);



            // White Collared Shirt V-Insert & Tie

            const shirtV = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.55, 8), whiteShirtMat);

            shirtV.position.set(0, 1.25, 0.35);

            const tie = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.50, 0.04), tieMat);

            tie.position.set(0, 1.15, 0.44);

            char.add(shirtV, tie);



            // Pelvis

            const pelvis = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.42, 0.35, 14), suitMat);

            pelvis.position.y = 0.55;

            char.add(pelvis);



            // TWO ARTICULATED LEGS & SHOES (Natural vertical legs swinging when walking, bending 90 deg when seated)

            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.20, 0.52, 0);



            const lPants = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.10, 0.52, 10), suitMat);

            lPants.position.y = -0.25;

            const lShoe = new THREE.Mesh(createRoundedBoxGeometry(0.18, 0.12, 0.36, 0.04, 2), shoeMat);

            lShoe.position.set(0, -0.52, 0.06);

            leftLeg.add(lPants, lShoe);

            char.add(leftLeg);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.20, 0.52, 0);



            const rPants = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.10, 0.52, 10), suitMat);

            rPants.position.y = -0.25;

            const rShoe = new THREE.Mesh(createRoundedBoxGeometry(0.18, 0.12, 0.36, 0.04, 2), shoeMat);

            rShoe.position.set(0, -0.52, 0.06);

            rightLeg.add(rPants, rShoe);

            char.add(rightLeg);



            // Initial posture: Seated under executive desk

            leftLeg.rotation.x = -Math.PI / 2.2;

            rightLeg.rotation.x = -Math.PI / 2.2;



            // Head

            const headGroup = new THREE.Group();

            headGroup.name = 'head';

            headGroup.position.set(0, 1.95, 0);



            const headMesh = new THREE.Mesh(new THREE.SphereGeometry(0.46, 18, 18), skinMat);

            headGroup.add(headMesh);



            const hairMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.9 });

            const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.48, 18, 18, 0, Math.PI * 2, 0, Math.PI / 1.8), hairMat);

            headGroup.add(hairCap);



            // Round Black Glasses

            const glassesMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.2, metalness: 0.8 });

            const rimL = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.032, 8, 20), glassesMat);

            rimL.position.set(-0.20, 0.02, 0.46);

            const rimR = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.032, 8, 20), glassesMat);

            rimR.position.set(0.20, 0.02, 0.46);

            const bridge = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.03, 0.02), glassesMat);

            bridge.position.set(0, 0.02, 0.46);

            headGroup.add(rimL, rimR, bridge);



            // Eyes

            const eyeMat = new THREE.MeshBasicMaterial({ color: 0x000000 });

            const eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 8), eyeMat);

            eyeL.position.set(-0.20, 0.02, 0.45);

            const eyeR = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 8), eyeMat);

            eyeR.position.set(0.20, 0.02, 0.45);

            headGroup.add(eyeL, eyeR);



            // Two Ears on sides

            for (let side of [-1, 1]) {

                const ear = new THREE.Mesh(new THREE.SphereGeometry(0.10, 8, 8), skinMat);

                ear.scale.set(0.35, 0.85, 0.7);

                ear.position.set(side * 0.45, 0.02, 0.02);

                headGroup.add(ear);

            }



            // Friendly Smile

            const mouthSmile = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.015, 4, 10, Math.PI), new THREE.MeshBasicMaterial({ color: 0x991b1b }));

            mouthSmile.position.set(0, -0.14, 0.44);

            headGroup.add(mouthSmile);



            char.add(headGroup);



            // NATURAL FORWARD ARMS (NEGATIVE ROTATION X = SWINGS FORWARD TOWARDS DESK & IPAD!)

            const leftArm = new THREE.Group();

            leftArm.name = 'leftArm';

            leftArm.position.set(-0.46, 1.35, 0.15); // Shoulder pivot

            const lArmMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.52, 8), suitMat);

            lArmMesh.position.y = -0.26;

            const lCuff = new THREE.Mesh(new THREE.CylinderGeometry(0.115, 0.115, 0.08, 8), whiteShirtMat);

            lCuff.position.y = -0.50;

            const lHand = new THREE.Mesh(new THREE.SphereGeometry(0.10, 8, 8), skinMat);

            lHand.position.y = -0.56;

            leftArm.add(lArmMesh, lCuff, lHand);

            // NEGATIVE ROTATION.X POINTS FORWARD (+Z) ONTO DESK & IPAD!

            leftArm.rotation.x = -0.75;

            leftArm.rotation.y = -0.22;

            leftArm.rotation.z = -0.10;

            char.add(leftArm);



            const rightArm = new THREE.Group();

            rightArm.name = 'rightArm';

            rightArm.position.set(0.46, 1.35, 0.15);

            const rArmMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.52, 8), suitMat);

            rArmMesh.position.y = -0.26;

            const rCuff = new THREE.Mesh(new THREE.CylinderGeometry(0.115, 0.115, 0.08, 8), whiteShirtMat);

            rCuff.position.y = -0.50;

            const rHand = new THREE.Mesh(new THREE.SphereGeometry(0.10, 8, 8), skinMat);

            rHand.position.y = -0.56;

            rightArm.add(rArmMesh, rCuff, rHand);

            rightArm.rotation.x = -0.75;

            rightArm.rotation.y = 0.22;

            rightArm.rotation.z = 0.10;

            char.add(rightArm);



            return char;

        }



        // =========================================================================

        // 10. BUILD ASSISTANTS: SEATED ON CHAIRS (NOT ON DESK), FORWARD ARMS

        // =========================================================================

        buildAssistants(assistants = [], secretaries = [], chiefSecretary = null) {

            // Fallback: Ensure 3 main Doraemon assistants are always present so desks are never empty

            if (!assistants || assistants.length === 0) {

                assistants = [

                    { id: 'asst_suneo', name: 'Trợ lý chức năng nhiệm vụ', nickname: 'Suneo' },

                    { id: 'asst_gian', name: 'Trợ lý An ninh mạng', nickname: 'Gian' },

                    { id: 'asst_shizuka', name: 'Trợ lý Quản lý rủi ro', nickname: 'Shizuka' },

                    { id: 'asst_doraemon', name: 'Trợ lý Nghiệp vụ thuế', nickname: 'Doraemon' }

                ];

            }



            for (const item of this.characters) {

                if (item.workstation) this.scene.remove(item.workstation);

                if (item.mesh) this.scene.remove(item.mesh);

            }

            this.characters = [];

            this.clickableObjects = [];

            this.takeCopterPropellers = [];



            // Tự động nạp lại toàn bộ mesh & bảng tên CIO Bắc Nguyễn vào clickableObjects

            if (this.nobita && this.nobita.character) {

                this.nobita.character.traverse((child) => {

                    if (child.isMesh || child.isSprite) {

                        this.clickableObjects.push(child);

                    }

                });

            }



            // BỐ TRÍ CÁC BÀN LÀM VIỆC TRỢ LÝ: KHÔNG BỐ TRÍ PHÍA TRƯỚC CIO BẮC NGUYỄN (Yêu cầu 2)

            // Toàn bộ khu vực trung tâm trước bàn CIO (x = -4.5 đến +4.5) để thông thoáng hoàn toàn!

            const workstationLayouts = [

                { x: -8.0, z: 4.5, rot: 0 },             // Cánh trái trước (Suneo)

                { x: -8.0, z: 0.5, rot: 0 },             // Cánh trái giữa (Gian) - ngồi bên cánh, không chắn trước CIO!

                { x: 8.0, z: 4.5, rot: 0 },              // Cánh phải trước (Shizuka)

                { x: 8.0, z: 0.5, rot: 0 },              // Cánh phải giữa (Doraemon)

                { x: -12.0, z: 4.5, rot: 0 },            // Cánh trái ngoài trước

                { x: -12.0, z: 0.5, rot: 0 },            // Cánh trái ngoài giữa

                { x: -12.0, z: -5.5, rot: Math.PI / 2 }, // Cánh trái sát tường

                { x: 12.0, z: 3.5, rot: 0 }              // Cánh phải ngoài

            ];



            const usedKeys = [];



            assistants.forEach((asst, index) => {

                const layout = workstationLayouts[index % workstationLayouts.length];

                const charData = matchCharacter(asst.nickname, index, usedKeys);

                usedKeys.push(charData.key);



                // 1. Realistic Workstation Desk (Open legroom underneath!)

                const workstation = this.buildWorkstation(layout.x, 0, layout.z, layout.rot, charData, asst);

                this.scene.add(workstation);



                // 2. Calculate Exact Chair Sitting Position (z = -0.48 in local workstation space)

                // Character sits ON the chair cushion, NOT on top of the desk!

                const chairOffset = new THREE.Vector3(0, 0, -0.48);

                chairOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), layout.rot);

                const seatedWorldPos = new THREE.Vector3(layout.x + chairOffset.x, 0.10, layout.z + chairOffset.z);



                // 3. Character Model

                const charModel = this.buildCharacterModel(charData);

                charModel.position.copy(seatedWorldPos);

                charModel.rotation.y = layout.rot;



                // FLOATING BADGE: DOUBLE-SIZED SUBTITLE (36px font) & RAISED TO y = 3.8

                const nameBadge = createFloatingNameBadge(charData.name, asst.name, false);

                nameBadge.position.set(0, 3.8, 0);

                charModel.add(nameBadge);



                // Thinking Lightbulb (💡)

                const lightbulb = createThinkingLightbulb();

                charModel.add(lightbulb);



                this.scene.add(charModel);



                charModel.traverse((child) => {

                    if (child.isMesh || child.isSprite) {

                        child.userData = {

                            isAssistant: true,

                            assistantId: asst.id,

                            assistantName: asst.name,

                            characterName: charData.name,

                            role: asst.name || charData.role,

                            charData: charData,

                            asst: asst

                        };

                        this.clickableObjects.push(child);

                    }

                });



                this.characters.push({

                    id: asst.id,

                    name: asst.name,

                    characterName: charData.name,

                    charData: charData,

                    mesh: charModel,

                    badgeSprite: nameBadge,

                    workstation: workstation,

                    homePos: seatedWorldPos.clone(),

                    homeRot: layout.rot,

                    state: 'working',

                    stateTime: 0,

                    targetPos: seatedWorldPos.clone(),

                    speed: 2.1 + Math.random() * 0.4,

                    lightbulb: lightbulb,

                    leftArm: charModel.getObjectByName('leftArm'),

                    rightArm: charModel.getObjectByName('rightArm'),

                    leftLeg: charModel.getObjectByName('leftLeg'),

                    rightLeg: charModel.getObjectByName('rightLeg'),

                    head: charModel.getObjectByName('head'),

                    walkPath: []

                });

            });



            // 2. DỰNG CÁC THƯ KÝ AI TIN TỨC (VỊ TRÍ NGỒI PHÍA TƯỜNG XA - NHÂN VẬT CỔ TÍCH VIỆT NAM)

            if (secretaries && secretaries.length > 0) {

                this.secretariesList = secretaries;

                const secretaryLayouts = [

                    { x: -5.0, z: -13.5, rot: 0 },

                    { x: 5.0, z: -13.5, rot: 0 },

                    { x: 0.0, z: -13.8, rot: 0 },

                    { x: -9.5, z: -13.5, rot: 0 },

                    { x: -2.5, z: -13.5, rot: 0 },

                    { x: 2.5, z: -13.5, rot: 0 },

                    { x: 9.5, z: -13.5, rot: 0 }

                ];



                secretaries.forEach((sec, sIdx) => {

                    const sLayout = secretaryLayouts[sIdx % secretaryLayouts.length];

                    const baseFairy = matchFairyTaleCharacter(sec.character || sec.name, sIdx);

                    const fairyChar = Object.assign({}, baseFairy, {

                        appearance: sec.appearance || '',

                        secData: sec

                    });



                    const sWorkstation = this.buildWorkstation(sLayout.x, 0, sLayout.z, sLayout.rot, fairyChar, sec);

                    this.scene.add(sWorkstation);



                    const sChairOffset = new THREE.Vector3(0, 0, -0.48);

                    sChairOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), sLayout.rot);

                    const sSeatedWorldPos = new THREE.Vector3(sLayout.x + sChairOffset.x, 0.10, sLayout.z + sChairOffset.z);



                    const sCharModel = this.buildCharacterModel(fairyChar);

                    sCharModel.position.copy(sSeatedWorldPos);

                    sCharModel.rotation.y = sLayout.rot;



                    const sBadge = createFloatingNameBadge(fairyChar.name, sec.role || sec.name, 'secretary');

                    sBadge.position.set(0, 3.8, 0);

                    sCharModel.add(sBadge);



                    const sLightbulb = createThinkingLightbulb();

                    sCharModel.add(sLightbulb);



                    this.scene.add(sCharModel);



                    sCharModel.traverse((child) => {

                        if (child.isMesh || child.isSprite) {

                            child.userData = {

                                isSecretary: true,

                                isAssistant: true,

                                secretaryId: sec.id,

                                secretaryName: sec.name,

                                characterName: fairyChar.name,

                                appearance: sec.appearance || '',

                                role: sec.role || fairyChar.badge,

                                scheduledTime: sec.scheduled_time || '08:00',

                                charData: fairyChar,

                                sec: sec

                            };

                            this.clickableObjects.push(child);

                        }

                    });



                    this.characters.push({

                        id: sec.id,

                        name: sec.name,

                        isSecretary: true,

                        characterName: fairyChar.name,

                        charData: fairyChar,

                        mesh: sCharModel,

                        badgeSprite: sBadge,

                        workstation: sWorkstation,

                        homePos: sSeatedWorldPos.clone(),

                        homeRot: sLayout.rot,

                        state: 'working',

                        stateTime: 0,

                        targetPos: sSeatedWorldPos.clone(),

                        speed: 2.1 + Math.random() * 0.4,

                        lightbulb: sLightbulb,

                        leftArm: sCharModel.getObjectByName('leftArm'),

                        rightArm: sCharModel.getObjectByName('rightArm'),

                        leftLeg: sCharModel.getObjectByName('leftLeg'),

                        rightLeg: sCharModel.getObjectByName('rightLeg'),

                        head: sCharModel.getObjectByName('head'),

                        walkPath: []

                    });

                });

            }



            // =========================================================================

            // 3. DỰNG TỔNG THƯ KÝ CÔ TẤM (NHÂN VẬT ĐỘC LẬP TẠI MỤC THƯ KÝ NHẮC VIỆC)

            // =========================================================================

            const chiefCfg = chiefSecretary || window.__lastChiefConfig || {

                secretary_name: "Tổng thư ký Cô Tấm",

                secretary_role: "Thư ký Nhắc việc & Lịch trình",

                secretary_appearance: "Nữ tổng thư ký dịu dàng, áo tứ thân lụa hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao, nói giọng nữ tiếng việt miền nam."

            };

            window.__lastChiefConfig = chiefCfg;



            const chiefLayout = { x: 4.2, z: -3.0, rot: -Math.PI / 10 };

            const coTamCharData = {

                key: 'chief_co_tam',

                name: chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm',

                role: chiefCfg.secretary_role || 'Thư ký Nhắc việc & Lịch trình',

                badge: 'Tổng Thư Ký',

                appearance: chiefCfg.secretary_appearance || 'Nữ tổng thư ký dịu dàng, áo tứ thân lụa hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao, nói giọng nữ tiếng việt miền nam.',

                avatar: '🌸',

                color: 0xec4899,

                type: 'chief_co_tam'

            };



            const chiefWorkstation = this.buildChiefWorkstation(chiefLayout.x, 0, chiefLayout.z, chiefLayout.rot, coTamCharData);

            this.scene.add(chiefWorkstation);



            const chiefChairOffset = new THREE.Vector3(0, 0, -0.48);

            chiefChairOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), chiefLayout.rot);

            const chiefSeatedWorldPos = new THREE.Vector3(chiefLayout.x + chiefChairOffset.x, 0.10, chiefLayout.z + chiefChairOffset.z);



            const chiefCharModel = this.buildCoTamMesh(chiefCfg);

            chiefCharModel.position.copy(chiefSeatedWorldPos);

            chiefCharModel.rotation.y = chiefLayout.rot;



            // Bảng tên nổi đặc biệt VIP dành cho Tổng thư ký Cô Tấm

            const chiefBadge = createFloatingNameBadge(chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm', chiefCfg.secretary_role || 'Thư ký Nhắc việc & Lịch trình', 'chief_secretary');

            chiefBadge.position.set(0, 3.85, 0);

            chiefCharModel.add(chiefBadge);



            const chiefLightbulb = createThinkingLightbulb();

            chiefCharModel.add(chiefLightbulb);



            this.scene.add(chiefCharModel);



            chiefCharModel.traverse((child) => {

                if (child.isMesh || child.isSprite) {

                    child.userData = {

                        isChiefSecretary: true,

                        isAssistant: true,

                        id: 'chief_co_tam',

                        name: chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm',

                        characterName: chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm',

                        role: chiefCfg.secretary_role || 'Thư ký Nhắc việc & Lịch trình',

                        appearance: chiefCfg.secretary_appearance,

                        charData: coTamCharData,

                        chiefConfig: chiefCfg

                    };

                    this.clickableObjects.push(child);

                }

            });



            this.characters.push({

                id: 'chief_co_tam',

                name: chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm',

                characterName: chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm',

                isChiefSecretary: true,

                charData: coTamCharData,

                mesh: chiefCharModel,

                badgeSprite: chiefBadge,

                workstation: chiefWorkstation,

                homePos: chiefSeatedWorldPos.clone(),

                homeRot: chiefLayout.rot,

                state: 'working',

                stateTime: 0,

                targetPos: chiefSeatedWorldPos.clone(),

                speed: 2.1,

                lightbulb: chiefLightbulb,

                leftArm: chiefCharModel.getObjectByName('leftArm'),

                rightArm: chiefCharModel.getObjectByName('rightArm'),

                leftLeg: chiefCharModel.getObjectByName('leftLeg'),

                rightLeg: chiefCharModel.getObjectByName('rightLeg'),

                head: chiefCharModel.getObjectByName('head'),

                walkPath: []

            });

        }



        // DỰNG MÔ HÌNH 3D ĐỘC QUYỀN TỔNG THƯ KÝ CÔ TẤM (ÁO TỨ THÂN HỒNG CÁNH SEN, NÓN QUAI THAO, HOA SEN CÀI TÓC)

        buildCoTamMesh(chiefConfig = {}) {

            const group = new THREE.Group();

            group.name = 'chiefCoTamRoot';



            const skinMat = new THREE.MeshStandardMaterial({ color: 0xfff0ea, roughness: 0.55 });

            const hairMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.4 });

            const lotusPinkMat = new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.5 }); // Áo tứ thân hồng cánh sen

            const lotusDeepMat = new THREE.MeshStandardMaterial({ color: 0xdb2777, roughness: 0.5 }); // Tà viền áo

            const yemMat = new THREE.MeshStandardMaterial({ color: 0xfff1f2, roughness: 0.4 });      // Yếm đào lụa

            const silkSashMat = new THREE.MeshStandardMaterial({ color: 0x2dd4bf, roughness: 0.4 }); // Dải lụa xanh ngọc

            const goldSashMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, metalness: 0.6, roughness: 0.3 }); // Khăn bao vàng

            const skirtMat = new THREE.MeshStandardMaterial({ color: 0x18181b, roughness: 0.6 });    // Váy lụa dài đen

            const hatStrawMat = new THREE.MeshStandardMaterial({ color: 0xfef08a, roughness: 0.7 }); // Nan tre vàng nón quai thao

            const hatRimMat = new THREE.MeshStandardMaterial({ color: 0xd97706, roughness: 0.6 });   // Viền nẹp nón

            const eyeWhiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

            const pupilMat = new THREE.MeshBasicMaterial({ color: 0x09090b });

            const lipMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e });



            // Vóc dáng thanh thoát, cao ráo, mềm mại

            group.scale.set(0.95, 1.05, 0.95);



            // 1. Thân áo tứ thân (Torso)

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.34, 0.90, 14), lotusPinkMat);

            torso.position.y = 1.0;

            torso.castShadow = true;

            group.add(torso);



            // Cổ yếm đào trắng ngà bên trong lấp ló

            const yem = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.40, 8), yemMat);

            yem.position.set(0, 1.25, 0.24);

            group.add(yem);



            // 2 tà trước vạt chéo tứ thân buông lơi

            const flapL = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.55, 0.04), lotusDeepMat);

            flapL.position.set(-0.12, 0.65, 0.22);

            flapL.rotation.z = -0.15;

            const flapR = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.55, 0.04), lotusDeepMat);

            flapR.position.set(0.12, 0.65, 0.22);

            flapR.rotation.z = 0.15;

            group.add(flapL, flapR);



            // Dải lụa thắt lưng ngọc bích / vàng tơ thắt ngang eo

            const sash1 = new THREE.Mesh(new THREE.CylinderGeometry(0.39, 0.39, 0.10, 14), silkSashMat);

            sash1.position.y = 0.82;

            const sash2 = new THREE.Mesh(new THREE.CylinderGeometry(0.395, 0.395, 0.05, 14), goldSashMat);

            sash2.position.y = 0.78;

            group.add(sash1, sash2);



            // Dải quai lụa buông rủ bên hông

            const ribbon = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.45, 0.02), silkSashMat);

            ribbon.position.set(0.24, 0.58, 0.20);

            ribbon.rotation.z = 0.12;

            group.add(ribbon);



            // 2. Chân váy lụa đen dài tha thướt

            const skirt = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.48, 0.70, 14), skirtMat);

            skirt.position.y = 0.40;

            group.add(skirt);



            // 3. Hai chân khớp động

            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.16, 0.45, 0);

            const lLegMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.45, 8), skirtMat);

            lLegMesh.position.y = -0.22;

            const lShoe = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.08, 0.24), lotusDeepMat);

            lShoe.position.set(0, -0.45, 0.04);

            leftLeg.add(lLegMesh, lShoe);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.16, 0.45, 0);

            const rLegMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.45, 8), skirtMat);

            rLegMesh.position.y = -0.22;

            const rShoe = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.08, 0.24), lotusDeepMat);

            rShoe.position.set(0, -0.45, 0.04);

            rightLeg.add(rLegMesh, rShoe);



            // Khi ngồi ghế: chân gập tự nhiên

            leftLeg.rotation.x = -Math.PI / 2.3;

            rightLeg.rotation.x = -Math.PI / 2.3;

            group.add(leftLeg, rightLeg);



            // 4. Hai cánh tay áo lụa hồng cử động

            const leftArm = new THREE.Group();

            leftArm.name = 'leftArm';

            leftArm.position.set(-0.46, 1.35, 0);

            const lArmSleeve = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.50, 10), lotusPinkMat);

            lArmSleeve.position.y = -0.22;

            const lHand = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 8), skinMat);

            lHand.position.y = -0.48;

            leftArm.add(lArmSleeve, lHand);



            const rightArm = new THREE.Group();

            rightArm.name = 'rightArm';

            rightArm.position.set(0.46, 1.35, 0);

            const rArmSleeve = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.50, 10), lotusPinkMat);

            rArmSleeve.position.y = -0.22;

            const rHand = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 8), skinMat);

            rHand.position.y = -0.48;

            rightArm.add(rArmSleeve, rHand);



            leftArm.rotation.x = -0.6;

            rightArm.rotation.x = -0.6;

            group.add(leftArm, rightArm);



            // 5. Đầu, Gương mặt thanh tú & Cổ

            const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.13, 0.22, 10), skinMat);

            neck.position.y = 1.48;

            group.add(neck);



            const head = new THREE.Group();

            head.name = 'head';

            head.position.set(0, 1.76, 0);



            const headMesh = new THREE.Mesh(new THREE.SphereGeometry(0.32, 18, 18), skinMat);

            headMesh.scale.set(0.95, 1.05, 0.95);

            head.add(headMesh);



            // Mắt bồ câu dịu dàng

            for (let side of [-1, 1]) {

                const eyeW = new THREE.Mesh(new THREE.SphereGeometry(0.065, 8, 8), eyeWhiteMat);

                eyeW.scale.set(0.8, 1.2, 0.3);

                eyeW.position.set(side * 0.10, 0.04, 0.29);

                const eyeP = new THREE.Mesh(new THREE.SphereGeometry(0.038, 8, 8), pupilMat);

                eyeP.position.set(side * 0.10, 0.04, 0.31);

                head.add(eyeW, eyeP);

            }



            // Nụ cười đoan trang

            const lips = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.02, 0.02), lipMat);

            lips.position.set(0, -0.12, 0.30);

            head.add(lips);



            // 6. Mái tóc dài thướt tha buông sau lưng

            const hairTop = new THREE.Mesh(new THREE.SphereGeometry(0.34, 16, 16), hairMat);

            hairTop.scale.set(1.0, 1.08, 1.05);

            hairTop.position.set(0, 0.04, -0.04);

            head.add(hairTop);



            // Tóc dài chảy dài xuống sau lưng

            const hairFlow = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.14, 0.85, 12), hairMat);

            hairFlow.position.set(0, -0.45, -0.22);

            hairFlow.rotation.x = 0.12;

            head.add(hairFlow);



            // 7. Bông hoa sen hồng cài tóc bên tai phải

            const lotusFlower = new THREE.Group();

            lotusFlower.position.set(0.32, 0.10, 0.12);

            lotusFlower.rotation.z = -0.3;

            const stamen = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 8), new THREE.MeshStandardMaterial({ color: 0xfacc15 }));

            lotusFlower.add(stamen);

            for (let p = 0; p < 6; p++) {

                const petal = new THREE.Mesh(new THREE.SphereGeometry(0.045, 6, 6), new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.3 }));

                petal.scale.set(0.5, 1.3, 0.4);

                const pAngle = (p / 6) * Math.PI * 2;

                petal.position.set(Math.cos(pAngle) * 0.04, Math.sin(pAngle) * 0.04, 0.01);

                petal.rotation.z = pAngle;

                lotusFlower.add(petal);

            }

            head.add(lotusFlower);



            // 8. Nón quai thao truyền thống Việt Nam

            const nonQuaiThao = new THREE.Group();

            nonQuaiThao.position.set(0, 0.35, 0.02);

            nonQuaiThao.rotation.x = -0.18;

            const hatDisk = new THREE.Mesh(new THREE.CylinderGeometry(0.56, 0.56, 0.03, 32), hatStrawMat);

            const hatRim = new THREE.Mesh(new THREE.TorusGeometry(0.56, 0.025, 8, 32), hatRimMat);

            hatRim.rotation.x = Math.PI / 2;

            const hatTop = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.28, 0.06, 24), hatStrawMat);

            hatTop.position.y = 0.03;

            nonQuaiThao.add(hatDisk, hatRim, hatTop);



            const quaiThaoL = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.55, 0.01), silkSashMat);

            quaiThaoL.position.set(-0.35, -0.30, 0.02);

            quaiThaoL.rotation.z = -0.15;

            const quaiThaoR = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.55, 0.01), silkSashMat);

            quaiThaoR.position.set(0.35, -0.30, 0.02);

            quaiThaoR.rotation.z = 0.15;

            nonQuaiThao.add(quaiThaoL, quaiThaoR);



            head.add(nonQuaiThao);

            group.add(head);



            return group;

        }



        // BÀN LÀM VIỆC SANG TRỌNG VIP CỦA TỔNG THƯ KÝ CÔ TẤM

        buildChiefWorkstation(x, y, z, rot, charData) {

            const group = new THREE.Group();

            group.position.set(x, y, z);

            group.rotation.y = rot;



            const woodMat = new THREE.MeshStandardMaterial({ color: 0xc89d68, roughness: 0.45 });

            const legMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.5, roughness: 0.4 });

            const leatherMat = new THREE.MeshStandardMaterial({ color: 0xdb2777, roughness: 0.6 });



            // Mặt bàn sang trọng gỗ sồi tự nhiên

            const topGeo = createRoundedBoxGeometry(2.4, 0.06, 1.1, 0.10, 3);

            const deskTop = new THREE.Mesh(topGeo, woodMat);

            deskTop.position.set(0, 0.75, 0.38);

            deskTop.castShadow = true;

            group.add(deskTop);



            // Chân bàn

            for (let sideX of [-1.05, 1.05]) {

                for (let sideZ of [-0.05, 0.85]) {

                    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.72, 8), legMat);

                    leg.position.set(sideX, 0.36, sideZ);

                    group.add(leg);

                }

            }



            // Bình hoa sen hồng trên bàn

            const vase = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.09, 0.18, 12), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2 }));

            vase.position.set(-0.85, 0.87, 0.45);

            const flower = new THREE.Mesh(new THREE.SphereGeometry(0.06, 8, 8), new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.3 }));

            flower.position.set(-0.85, 0.98, 0.45);

            group.add(vase, flower);



            // Laptop mỏng nhẹ màu bạc hồng

            const laptopBase = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.015, 0.26), new THREE.MeshStandardMaterial({ color: 0xfbcfe8, metalness: 0.8, roughness: 0.2 }));

            laptopBase.position.set(0, 0.79, 0.40);

            const laptopScreen = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.24, 0.015), new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.3 }));

            laptopScreen.position.set(0, 0.91, 0.52);

            laptopScreen.rotation.x = -0.22;

            group.add(laptopBase, laptopScreen);



            // Sổ công tác bìa da

            const notebook = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.02, 0.32), new THREE.MeshStandardMaterial({ color: 0x831843, roughness: 0.5 }));

            notebook.position.set(0.65, 0.79, 0.35);

            notebook.rotation.y = 0.15;

            group.add(notebook);



            // Ghế bọc da lụa hồng của Tổng thư ký

            const chair = new THREE.Group();

            chair.position.set(0, 0, -0.48);

            const seat = new THREE.Mesh(createRoundedBoxGeometry(0.56, 0.08, 0.54, 0.06, 2), leatherMat);

            seat.position.y = 0.46;

            const back = new THREE.Mesh(createRoundedBoxGeometry(0.54, 0.65, 0.06, 0.06, 2), leatherMat);

            back.position.set(0, 0.80, -0.24);

            const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.42, 8), legMat);

            post.position.y = 0.21;

            chair.add(seat, back, post);

            group.add(chair);



            return group;

        }





        // REALISTIC WORKSTATION: Tabletop at y = 0.80, legs on sides, OPEN LEGROOM UNDERNEATH!

        buildWorkstation(x, y, z, rot, charData, asst) {

            const group = new THREE.Group();

            group.position.set(x, y, z);

            group.rotation.y = rot;



            const deskMat = new THREE.MeshStandardMaterial({ color: 0xdeb887, roughness: 0.5 });

            const legMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.6, roughness: 0.4 });



            // 1. Tabletop (Width 2.6m, Depth 1.2m, Thickness 6cm, Surface at y = 0.78m)

            const topGeo = createRoundedBoxGeometry(2.6, 0.06, 1.2, 0.12, 3);

            const deskTop = new THREE.Mesh(topGeo, deskMat);

            deskTop.position.set(0, 0.75, 0.40); // Extends from z = -0.20 to z = +1.0

            deskTop.castShadow = true;

            group.add(deskTop);



            // 2. Left & Right Desk Legs (Open knee space in the middle for chair & legs!)

            const legL = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.72, 1.0), legMat);

            legL.position.set(-1.22, 0.36, 0.40);

            const legR = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.72, 1.0), legMat);

            legR.position.set(1.22, 0.36, 0.40);

            group.add(legL, legR);



            // 3. Frosted Partition Screen (At far side of desk z = 1.0)

            const part = new THREE.Mesh(createRoundedBoxGeometry(2.6, 0.55, 0.05, 0.03, 2), new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.75 }));

            part.position.set(0, 1.05, 1.0);

            group.add(part);



            // 4. LCD Monitor on Stand (Facing -Z toward assistant on chair)

            const monStand = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.15, 0.18), new THREE.MeshStandardMaterial({ color: 0x1e293b }));

            monStand.position.set(0, 0.85, 0.72);

            const monCase = new THREE.Mesh(createRoundedBoxGeometry(1.4, 0.85, 0.06, 0.04, 2), new THREE.MeshStandardMaterial({ color: 0x0f172a }));

            monCase.position.set(0, 1.35, 0.72);

            const monGlow = new THREE.Mesh(new THREE.PlaneGeometry(1.32, 0.77), new THREE.MeshBasicMaterial({ color: charData.color || 0x0284c7 }));

            monGlow.position.set(0, 1.35, 0.685);

            group.add(monStand, monCase, monGlow);



            // 5. Keyboard & Dorayaki Plate (Resting on desktop at y = 0.79)

            const kbMat = new THREE.MeshStandardMaterial({ color: 0x334155 });

            const keyboard = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.02, 0.28), kbMat);

            keyboard.position.set(0, 0.79, 0.18);

            group.add(keyboard);



            const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.03, 16), new THREE.MeshStandardMaterial({ color: 0xffffff }));

            plate.position.set(-0.80, 0.79, 0.25);

            const bun = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 12), new THREE.MeshStandardMaterial({ color: 0x92400e }));

            bun.scale.set(1.0, 0.45, 1.0);

            bun.position.set(-0.80, 0.83, 0.25);

            group.add(plate, bun);



            // 6. Ergonomic Workstation Chair (Positioned at z = -0.48 facing desk, seat at y = 0.45)

            const chair = buildStandardOfficeChair(0x1e293b);

            chair.position.set(0, 0, -0.48);

            group.add(chair);



            return group;

        }



        buildCharacterModel(charData) {

            const char = new THREE.Group();

            switch (charData.type) {

                case 'doraemon':

                    this.buildDoraemonMesh(char);

                    break;

                case 'shizuka':

                    this.buildShizukaMesh(char);

                    break;

                case 'suneo':

                    this.buildSuneoMesh(char);

                    break;

                case 'gian':

                    this.buildGianMesh(char);

                    break;

                case 'dorami':

                    this.buildDoramiMesh(char);

                    break;

                case 'fairy_tale':

                    this.buildFairyTaleCharacterMesh(char, charData);

                    break;

                default:

                    this.buildGenericAnimeMesh(char, charData);

                    break;

            }

            return char;

        }



        buildDoraemonMesh(group) {

            const blueMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.45 });

            const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.35 });

            const redMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.35 });

            const goldMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, metalness: 0.85, roughness: 0.25 });

            const blackMat = new THREE.MeshBasicMaterial({ color: 0x0f172a });

            const mouthRedMat = new THREE.MeshBasicMaterial({ color: 0xb91c1c });

            const tongueMat = new THREE.MeshBasicMaterial({ color: 0xf472b6 });



            // Blue Body

            const body = new THREE.Mesh(new THREE.SphereGeometry(0.55, 20, 20), blueMat);

            body.position.y = 0.95;

            body.castShadow = true;

            group.add(body);



            // White Belly

            const belly = new THREE.Mesh(new THREE.SphereGeometry(0.44, 16, 16), whiteMat);

            belly.scale.set(1.0, 0.95, 0.65);

            belly.position.set(0, 0.92, 0.28);

            group.add(belly);



            // 4D Pocket (Pouch) on Belly (Media 4 Reference)

            const pocketGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.02, 16, 1, false, 0, Math.PI);

            const pocket = new THREE.Mesh(pocketGeo, new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.5 }));

            pocket.rotation.x = Math.PI / 2;

            pocket.rotation.z = Math.PI;

            pocket.position.set(0, 0.88, 0.54);

            const pocketRim = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.02, 0.02), blackMat);

            pocketRim.position.set(0, 0.88, 0.55);

            group.add(pocket, pocketRim);



            // Red Round Ball Tail on Back

            const tail = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 12), redMat);

            tail.position.set(0, 0.80, -0.56);

            group.add(tail);



            // Red Collar

            const collar = new THREE.Mesh(new THREE.TorusGeometry(0.48, 0.055, 10, 28), redMat);

            collar.rotation.x = Math.PI / 2;

            collar.position.set(0, 1.42, 0);



            // Gold Bell (Suzu) with Slit (Media 4 Reference)

            const bellGroup = new THREE.Group();

            bellGroup.position.set(0, 1.38, 0.48);

            const bell = new THREE.Mesh(new THREE.SphereGeometry(0.12, 14, 14), goldMat);

            const bellRim = new THREE.Mesh(new THREE.TorusGeometry(0.122, 0.015, 6, 16), blackMat);

            bellRim.rotation.x = Math.PI / 2;

            const bellHole = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 8), blackMat);

            bellHole.position.set(0, -0.04, 0.11);

            const bellSlit = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.06, 0.02), blackMat);

            bellSlit.position.set(0, -0.07, 0.11);

            bellGroup.add(bell, bellRim, bellHole, bellSlit);

            group.add(collar, bellGroup);



            // Blue Head

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.62, 22, 22), blueMat);

            head.name = 'head';

            head.position.set(0, 1.95, 0);

            head.castShadow = true;

            group.add(head);



            // White Oval Face Mask

            const face = new THREE.Mesh(new THREE.SphereGeometry(0.52, 20, 20), whiteMat);

            face.scale.set(1.0, 0.92, 0.72);

            face.position.set(0, 1.88, 0.28);

            group.add(face);



            // TWO LARGE ADJACENT WHITE EYES (Media 4 Reference)

            for (let side of [-1, 1]) {

                const eyeWhite = new THREE.Mesh(new THREE.SphereGeometry(0.15, 14, 14), whiteMat);

                eyeWhite.scale.set(0.85, 1.15, 0.40);

                eyeWhite.position.set(side * 0.125, 2.22, 0.52);



                const eyeOutline = new THREE.Mesh(new THREE.TorusGeometry(0.145, 0.015, 6, 20), blackMat);

                eyeOutline.scale.set(0.85, 1.15, 1.0);

                eyeOutline.position.set(side * 0.125, 2.22, 0.58);



                const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.065, 10, 10), blackMat);

                pupil.scale.set(0.9, 1.3, 0.3);

                pupil.position.set(side * 0.105, 2.20, 0.60);



                const glint = new THREE.Mesh(new THREE.SphereGeometry(0.022, 8, 8), whiteMat);

                glint.position.set(side * 0.105 + 0.02, 2.23, 0.63);



                group.add(eyeWhite, eyeOutline, pupil, glint);

            }



            // Shiny Red Nose (Sitting right between bottom of eyes)

            const nose = new THREE.Mesh(new THREE.SphereGeometry(0.095, 14, 14), redMat);

            nose.position.set(0, 2.05, 0.66);

            const noseGlint = new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 8), whiteMat);

            noseGlint.position.set(0.03, 2.08, 0.73);

            group.add(nose, noseGlint);



            // Vertical Line from Nose to Mouth

            const vLine = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.18, 0.01), blackMat);

            vLine.position.set(0, 1.94, 0.64);

            group.add(vLine);



            // WIDE CHEERFUL SMILING MOUTH (Media 4 Reference)

            const mouthGroup = new THREE.Group();

            mouthGroup.position.set(0, 1.82, 0.58);



            const mouthBg = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.02, 16, 1, false, 0, Math.PI), mouthRedMat);

            mouthBg.rotation.x = Math.PI / 2;

            mouthBg.rotation.z = Math.PI;

            mouthBg.position.set(0, 0, 0.04);



            const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 10), tongueMat);

            tongue.scale.set(1.2, 0.7, 0.4);

            tongue.position.set(0, -0.06, 0.06);



            const smileOutline = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.018, 6, 20, Math.PI), blackMat);

            smileOutline.position.set(0, 0, 0.05);



            mouthGroup.add(mouthBg, tongue, smileOutline);

            group.add(mouthGroup);



            // 6 Black Whiskers (3 on each cheek)

            for (let side of [-1, 1]) {

                const angles = [-0.15, 0, 0.15];

                for (let i = 0; i < 3; i++) {

                    const whisker = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.018, 0.01), blackMat);

                    whisker.rotation.z = side * angles[i];

                    whisker.position.set(side * 0.36, 1.94 + (i - 1) * 0.07, 0.58);

                    group.add(whisker);

                }

            }



            // Paws reaching forward onto desk

            const handGeo = new THREE.SphereGeometry(0.16, 12, 12);

            const handL = new THREE.Mesh(handGeo, whiteMat);

            handL.name = 'leftArm';

            handL.position.set(-0.50, 0.88, 0.40);

            const handR = new THREE.Mesh(handGeo, whiteMat);

            handR.name = 'rightArm';

            handR.position.set(0.50, 0.88, 0.40);

            group.add(handL, handR);



            // Two Iconic White Oval Feet

            const footL = new THREE.Mesh(new THREE.SphereGeometry(0.22, 14, 14), whiteMat);

            footL.scale.set(1.0, 0.45, 1.4);

            footL.position.set(-0.25, 0.10, 0.12);

            footL.name = 'leftLeg';

            const footR = new THREE.Mesh(new THREE.SphereGeometry(0.22, 14, 14), whiteMat);

            footR.scale.set(1.0, 0.45, 1.4);

            footR.position.set(0.25, 0.10, 0.12);

            footR.name = 'rightLeg';

            group.add(footL, footR);



            // Take-copter

            const takeCopterGroup = new THREE.Group();

            takeCopterGroup.position.set(0, 2.56, 0);

            const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.35, 8), goldMat);

            shaft.position.y = 0.17;

            const propeller = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.03, 0.12), goldMat);

            propeller.position.y = 0.35;

            takeCopterGroup.add(shaft, propeller);

            this.takeCopterPropellers.push(propeller);

            group.add(takeCopterGroup);

        }



        buildShizukaMesh(group) {

            const skinMat = new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.65 });

            const pinkMat = new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.5 });

            const blueMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.5 });

            const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });

            const hairMat = new THREE.MeshStandardMaterial({ color: 0x1c1917, roughness: 0.85 });

            const blackMat = new THREE.MeshBasicMaterial({ color: 0x09090b });

            const shoeMat = new THREE.MeshStandardMaterial({ color: 0xec4899, roughness: 0.4 });

            const sockMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });

            const mouthRed = new THREE.MeshBasicMaterial({ color: 0xbe123c });

            const tonguePink = new THREE.MeshBasicMaterial({ color: 0xfb7185 });

            const blushMat = new THREE.MeshBasicMaterial({ color: 0xfda4af });



            // Pink Sweater Torso

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.40, 0.38, 0.70, 14), pinkMat);

            torso.position.y = 1.15;

            group.add(torso);



            // White Pointed Collars (Media 2 Reference)

            const collarL = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.22, 4), whiteMat);

            collarL.position.set(-0.11, 1.48, 0.34);

            collarL.rotation.z = -0.4;

            collarL.rotation.x = -0.3;

            const collarR = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.22, 4), whiteMat);

            collarR.position.set(0.11, 1.48, 0.34);

            collarR.rotation.z = 0.4;

            collarR.rotation.x = -0.3;

            group.add(collarL, collarR);



            // Blue Skirt (Media 2 Reference)

            const skirt = new THREE.Mesh(new THREE.ConeGeometry(0.55, 0.45, 16), blueMat);

            skirt.position.y = 0.72;

            group.add(skirt);



            // Head Group

            const headGroup = new THREE.Group();

            headGroup.name = 'head';

            headGroup.position.set(0, 1.88, 0);



            // Skin Head Sphere

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.44, 18, 18), skinMat);

            headGroup.add(head);



            // Black Hair Cap (Back & Top)

            const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.46, 18, 18, 0, Math.PI * 2, 0, Math.PI / 1.7), hairMat);

            hairCap.position.y = 0.03;

            headGroup.add(hairCap);



            // Signature Front Bangs (3 bangs lock on forehead)

            const centerBang = new THREE.Mesh(new THREE.ConeGeometry(0.10, 0.28, 4), hairMat);

            centerBang.rotation.x = Math.PI - 0.25;

            centerBang.position.set(0, 0.28, 0.40);

            const bangL = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.32, 4), hairMat);

            bangL.rotation.x = Math.PI - 0.25;

            bangL.rotation.z = 0.35;

            bangL.position.set(-0.16, 0.25, 0.38);

            const bangR = new THREE.Mesh(new THREE.ConeGeometry(0.11, 0.32, 4), hairMat);

            bangR.rotation.x = Math.PI - 0.25;

            bangR.rotation.z = -0.35;

            bangR.position.set(0.16, 0.25, 0.38);

            headGroup.add(centerBang, bangL, bangR);



            // TWO EARS WITH INNER HELIX DETAIL (Media 2 Reference)

            for (let side of [-1, 1]) {

                const ear = new THREE.Mesh(new THREE.SphereGeometry(0.10, 10, 10), skinMat);

                ear.scale.set(0.4, 0.85, 0.7);

                ear.position.set(side * 0.42, 0.02, 0.04);

                const earInner = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.015, 4, 10, Math.PI), new THREE.MeshBasicMaterial({ color: 0xfca5a5 }));

                earInner.rotation.y = side * Math.PI / 2;

                earInner.position.set(side * 0.44, 0.02, 0.04);

                headGroup.add(ear, earInner);

            }



            // TWIN LOW PIGTAILS TIED BEHIND EARS (Media 2 Reference)

            for (let side of [-1, 1]) {

                const tie = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.02, 6, 12), new THREE.MeshBasicMaterial({ color: 0xef4444 }));

                tie.position.set(side * 0.42, -0.06, -0.15);

                const pigtail = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.03, 0.45, 8), hairMat);

                pigtail.position.set(side * 0.46, -0.25, -0.18);

                pigtail.rotation.z = side * -0.40;

                pigtail.rotation.x = -0.20;

                headGroup.add(tie, pigtail);

            }



            // BIG SPARKLING ANIME EYES (Media 2 Reference)

            for (let side of [-1, 1]) {

                const eyeWhite = new THREE.Mesh(new THREE.SphereGeometry(0.095, 12, 12), whiteMat);

                eyeWhite.scale.set(0.85, 1.25, 0.35);

                eyeWhite.position.set(side * 0.145, 0.06, 0.40);



                const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.065, 10, 10), blackMat);

                pupil.scale.set(0.80, 1.20, 0.30);

                pupil.position.set(side * 0.145, 0.06, 0.43);



                const glint = new THREE.Mesh(new THREE.SphereGeometry(0.022, 6, 6), whiteMat);

                glint.position.set(side * 0.145 + 0.018, 0.09, 0.45);



                const lash = new THREE.Mesh(new THREE.TorusGeometry(0.085, 0.012, 4, 12, Math.PI * 0.75), blackMat);

                lash.position.set(side * 0.145, 0.13, 0.42);

                lash.rotation.z = side * -0.2;



                const brow = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.015, 0.01), blackMat);

                brow.position.set(side * 0.145, 0.20, 0.38);

                brow.rotation.z = side * -0.15;



                const blush = new THREE.Mesh(new THREE.CircleGeometry(0.055, 10), blushMat);

                blush.position.set(side * 0.25, -0.06, 0.36);

                blush.rotation.y = side * 0.4;



                headGroup.add(eyeWhite, pupil, glint, lash, brow, blush);

            }



            // Cute Dot Nose

            const nose = new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 8), new THREE.MeshStandardMaterial({ color: 0xfca5a5 }));

            nose.position.set(0, -0.01, 0.44);

            headGroup.add(nose);



            // Sweet Smiling Mouth (Media 2 Reference)

            const mouth = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.02, 12, 1, false, 0, Math.PI), mouthRed);

            mouth.rotation.x = Math.PI / 2;

            mouth.rotation.z = Math.PI;

            mouth.position.set(0, -0.12, 0.42);

            const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 8), tonguePink);

            tongue.position.set(0, -0.14, 0.43);

            headGroup.add(mouth, tongue);



            group.add(headGroup);



            // Arms reaching forward onto desk

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.50, 8), pinkMat);

            armL.name = 'leftArm';

            armL.position.set(-0.42, 1.25, 0.12);

            armL.rotation.x = -0.80;

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.50, 8), pinkMat);

            armR.name = 'rightArm';

            armR.position.set(0.42, 1.25, 0.12);

            armR.rotation.x = -0.80;

            group.add(armL, armR);



            // Legs with white socks & pink shoes

            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.16, 0.45, 0);

            const lCalf = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.07, 0.45, 8), skinMat);

            lCalf.position.y = -0.20;

            const lSock = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.12, 8), sockMat);

            lSock.position.y = -0.36;

            const lShoe = new THREE.Mesh(createRoundedBoxGeometry(0.14, 0.10, 0.26, 0.03, 2), shoeMat);

            lShoe.position.set(0, -0.42, 0.04);

            leftLeg.add(lCalf, lSock, lShoe);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.16, 0.45, 0);

            const rCalf = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.07, 0.45, 8), skinMat);

            rCalf.position.y = -0.20;

            const rSock = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.12, 8), sockMat);

            rSock.position.y = -0.36;

            const rShoe = new THREE.Mesh(createRoundedBoxGeometry(0.14, 0.10, 0.26, 0.03, 2), shoeMat);

            rShoe.position.set(0, -0.42, 0.04);

            rightLeg.add(rCalf, rSock, rShoe);



            group.add(leftLeg, rightLeg);

        }



        buildSuneoMesh(group) {

            const skinMat = new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.7 });

            const tealMat = new THREE.MeshStandardMaterial({ color: 0x0d9488, roughness: 0.5 });

            const hairMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.8 });

            const shoeMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.4 });

            const blackMat = new THREE.MeshBasicMaterial({ color: 0x09090b });

            const whiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });



            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.38, 0.90, 12), tealMat);

            torso.position.y = 0.95;

            group.add(torso);



            const headGroup = new THREE.Group();

            headGroup.name = 'head';

            headGroup.position.set(0, 1.80, 0);



            const head = new THREE.Mesh(new THREE.SphereGeometry(0.42, 16, 16), skinMat);

            headGroup.add(head);



            // Suneo's 3 front hair spikes

            for (let i = 0; i < 3; i++) {

                const spike = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.52, 6), hairMat);

                spike.rotation.x = -Math.PI / 3.2;

                spike.rotation.z = (i - 1) * 0.32;

                spike.position.set((i - 1) * 0.20, 0.42, 0.20);

                headGroup.add(spike);

            }



            // Ears

            for (let side of [-1, 1]) {

                const ear = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 8), skinMat);

                ear.scale.set(0.35, 0.85, 0.7);

                ear.position.set(side * 0.40, 0.02, 0.02);

                headGroup.add(ear);

            }



            // Fox Eyes

            for (let side of [-1, 1]) {

                const eye = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.025, 0.01), blackMat);

                eye.position.set(side * 0.15, 0.08, 0.38);

                eye.rotation.z = side * -0.3;

                headGroup.add(eye);

            }



            // Fox Snout / Smile

            const mouth = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.30, 4), skinMat);

            mouth.rotation.x = Math.PI / 2;

            mouth.position.set(0, -0.06, 0.46);

            headGroup.add(mouth);



            group.add(headGroup);



            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.50, 8), tealMat);

            armL.name = 'leftArm';

            armL.position.set(-0.42, 1.25, 0.12);

            armL.rotation.x = -0.80;

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.08, 0.50, 8), tealMat);

            armR.name = 'rightArm';

            armR.position.set(0.42, 1.25, 0.12);

            armR.rotation.x = -0.80;

            group.add(armL, armR);



            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.16, 0.50, 0);

            const lPants = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.48, 8), tealMat);

            lPants.position.y = -0.22;

            const lShoe = new THREE.Mesh(createRoundedBoxGeometry(0.15, 0.10, 0.28, 0.03, 2), shoeMat);

            lShoe.position.set(0, -0.46, 0.05);

            leftLeg.add(lPants, lShoe);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.16, 0.50, 0);

            const rPants = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.48, 8), tealMat);

            rPants.position.y = -0.22;

            const rShoe = new THREE.Mesh(createRoundedBoxGeometry(0.15, 0.10, 0.28, 0.03, 2), shoeMat);

            rShoe.position.set(0, -0.46, 0.05);

            rightLeg.add(rPants, rShoe);



            group.add(leftLeg, rightLeg);

        }



        buildGianMesh(group) {

            const skinMat = new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.70 });

            const orangeMat = new THREE.MeshStandardMaterial({ color: 0xea580c, roughness: 0.55 });

            const chevronBrown = new THREE.MeshStandardMaterial({ color: 0x451a03, roughness: 0.6 });

            const blueJeansMat = new THREE.MeshStandardMaterial({ color: 0x1d4ed8, roughness: 0.65 });

            const sneakerBrown = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.5 });

            const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 });

            const blackMat = new THREE.MeshBasicMaterial({ color: 0x09090b });

            const mouthRed = new THREE.MeshBasicMaterial({ color: 0x991b1b });

            const tonguePink = new THREE.MeshBasicMaterial({ color: 0xf43f5e });



            // Sturdy Torso in Signature Orange Shirt (Media 3 Reference)

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.60, 0.56, 1.10, 16), orangeMat);

            torso.position.y = 1.10;

            torso.castShadow = true;

            group.add(torso);



            // SIGNATURE BROWN ZIGZAG CHEVRON BAND ACROSS CHEST (Media 3 Reference!)

            const chevronGroup = new THREE.Group();

            chevronGroup.position.set(0, 1.16, 0);

            for (let p = -3; p <= 3; p++) {

                const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.20, 0.08, 0.04), chevronBrown);

                stripe.position.set(p * 0.14, (p % 2 === 0 ? 0.05 : -0.05), 0.58);

                stripe.rotation.z = (p % 2 === 0 ? 0.55 : -0.55);

                chevronGroup.add(stripe);

            }

            // Small White Shirt Collar & Buttons (Media 3 Reference)

            for (let b = 0; b < 3; b++) {

                const btn = new THREE.Mesh(new THREE.SphereGeometry(0.025, 6, 6), whiteMat);

                btn.position.set(0, 1.35 - b * 0.18, 0.58);

                group.add(btn);

            }

            group.add(chevronGroup);



            // Head Group

            const headGroup = new THREE.Group();

            headGroup.name = 'head';

            headGroup.position.set(0, 2.05, 0);



            // Wide Sturdy Head

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.52, 20, 20), skinMat);

            head.scale.set(1.05, 1.0, 0.95);

            headGroup.add(head);



            // GIAN'S ICONIC JAGGED CROPPED BLACK HAIR & SERRATED BANGS (Media 3 Reference)

            const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.54, 20, 20, 0, Math.PI * 2, 0, Math.PI / 1.8), blackMat);

            hairCap.position.set(0, 0.04, -0.02);

            headGroup.add(hairCap);



            // 5 Jagged Hair Bangs Spikes across forehead

            for (let i = -2; i <= 2; i++) {

                const spike = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.18, 4), blackMat);

                spike.rotation.x = Math.PI - 0.2;

                spike.position.set(i * 0.14, 0.38, 0.44);

                headGroup.add(spike);

            }



            // TWO ROUND EARS WITH INNER HELIX (Media 3 Reference)

            for (let side of [-1, 1]) {

                const ear = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 10), skinMat);

                ear.scale.set(0.35, 0.9, 0.8);

                ear.position.set(side * 0.52, 0.04, 0.02);

                const earInner = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.018, 4, 10, Math.PI), new THREE.MeshBasicMaterial({ color: 0xfca5a5 }));

                earInner.rotation.y = side * Math.PI / 2;

                earInner.position.set(side * 0.54, 0.04, 0.02);

                headGroup.add(ear, earInner);

            }



            // GIAN'S SIGNATURE BULBOUS BUTTON NOSE (Media 3 Reference)

            const nose = new THREE.Mesh(new THREE.SphereGeometry(0.11, 14, 14), skinMat);

            nose.position.set(0, 0.08, 0.54);

            const noseLine = new THREE.Mesh(new THREE.TorusGeometry(0.08, 0.015, 4, 12, Math.PI * 0.8), blackMat);

            noseLine.rotation.x = -Math.PI / 2;

            noseLine.position.set(0, 0.16, 0.53);

            headGroup.add(nose, noseLine);



            // EXPRESSIVE EYES WITH THICK EYEBROWS (Media 3 Reference)

            for (let side of [-1, 1]) {

                const eyeWhite = new THREE.Mesh(new THREE.SphereGeometry(0.08, 10, 10), whiteMat);

                eyeWhite.scale.set(0.9, 1.1, 0.3);

                eyeWhite.position.set(side * 0.18, 0.18, 0.46);



                const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.045, 8, 8), blackMat);

                pupil.position.set(side * 0.18, 0.18, 0.49);



                const brow = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.04, 0.02), blackMat);

                brow.position.set(side * 0.20, 0.29, 0.44);

                brow.rotation.z = side * 0.25;



                headGroup.add(eyeWhite, pupil, brow);

            }



            // GIAN'S BIG LAUGHING OPEN MOUTH (Media 3 Reference)

            const mouthGroup = new THREE.Group();

            mouthGroup.position.set(0, -0.10, 0.48);

            const mouthCavity = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.02, 16, 1, false, 0, Math.PI), mouthRed);

            mouthCavity.rotation.x = Math.PI / 2;

            mouthCavity.rotation.z = Math.PI;

            const tongue = new THREE.Mesh(new THREE.SphereGeometry(0.10, 10, 10), tonguePink);

            tongue.scale.set(1.4, 0.8, 0.4);

            tongue.position.set(0, -0.05, 0.03);

            const mouthRim = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.02, 6, 16, Math.PI), blackMat);

            mouthRim.position.set(0, 0, 0.02);

            mouthGroup.add(mouthCavity, tongue, mouthRim);

            headGroup.add(mouthGroup);



            group.add(headGroup);



            // Arms reaching forward onto desk

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.12, 0.55, 8), orangeMat);

            armL.name = 'leftArm';

            armL.position.set(-0.64, 1.40, 0.15);

            armL.rotation.x = -0.80;

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.12, 0.55, 8), orangeMat);

            armR.name = 'rightArm';

            armR.position.set(0.64, 1.40, 0.15);

            armR.rotation.x = -0.80;

            group.add(armL, armR);



            // Legs with Blue Denim Pants & Brown Sneakers with White Soles

            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.24, 0.55, 0);

            const lPants = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.14, 0.50, 10), blueJeansMat);

            lPants.position.y = -0.24;

            const lShoe = new THREE.Mesh(createRoundedBoxGeometry(0.22, 0.12, 0.36, 0.04, 2), sneakerBrown);

            lShoe.position.set(0, -0.50, 0.06);

            const lSole = new THREE.Mesh(new THREE.BoxGeometry(0.23, 0.03, 0.38), whiteMat);

            lSole.position.set(0, -0.56, 0.06);

            leftLeg.add(lPants, lShoe, lSole);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.24, 0.55, 0);

            const rPants = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.14, 0.50, 10), blueJeansMat);

            rPants.position.y = -0.24;

            const rShoe = new THREE.Mesh(createRoundedBoxGeometry(0.22, 0.12, 0.36, 0.04, 2), sneakerBrown);

            rShoe.position.set(0, -0.50, 0.06);

            const rSole = new THREE.Mesh(new THREE.BoxGeometry(0.23, 0.03, 0.38), whiteMat);

            rSole.position.set(0, -0.56, 0.06);

            rightLeg.add(rPants, rShoe, rSole);



            group.add(leftLeg, rightLeg);

        }



        buildDoramiMesh(group) {

            const yellowMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.5 });

            const redMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.4 });

            const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 });



            const body = new THREE.Mesh(new THREE.SphereGeometry(0.52, 18, 18), yellowMat);

            body.position.y = 0.95;

            group.add(body);



            const head = new THREE.Mesh(new THREE.SphereGeometry(0.56, 18, 18), yellowMat);

            head.position.set(0, 1.90, 0);

            group.add(head);



            const bowL = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.55, 8), redMat);

            bowL.rotation.z = Math.PI / 2.2;

            bowL.position.set(-0.32, 2.48, 0);

            const bowR = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.55, 8), redMat);

            bowR.rotation.z = -Math.PI / 2.2;

            bowR.position.x = 0.32;

            group.add(bowL, bowR);



            const armL = new THREE.Mesh(new THREE.SphereGeometry(0.14, 10, 10), whiteMat);

            armL.name = 'leftArm';

            armL.position.set(-0.48, 0.88, 0.35);

            const armR = new THREE.Mesh(new THREE.SphereGeometry(0.14, 10, 10), whiteMat);

            armR.name = 'rightArm';

            armR.position.set(0.48, 0.88, 0.35);

            group.add(armL, armR);



            const footL = new THREE.Mesh(new THREE.SphereGeometry(0.20, 14, 14), whiteMat);

            footL.scale.set(1.0, 0.45, 1.3);

            footL.position.set(-0.22, 0.10, 0.1);

            footL.name = 'leftLeg';

            const footR = new THREE.Mesh(new THREE.SphereGeometry(0.20, 14, 14), whiteMat);

            footR.scale.set(1.0, 0.45, 1.3);

            footR.position.set(0.22, 0.10, 0.1);

            footR.name = 'rightLeg';

            group.add(footL, footR);

        }



        buildGenericAnimeMesh(group, charData) {

            const skinMat = new THREE.MeshStandardMaterial({ color: 0xffedd5, roughness: 0.7 });

            const suitMat = new THREE.MeshStandardMaterial({ color: charData.color || 0x475569, roughness: 0.6 });

            const shoeMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.4 });



            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.40, 0.95, 14), suitMat);

            torso.position.y = 1.0;

            group.add(torso);



            const head = new THREE.Mesh(new THREE.SphereGeometry(0.44, 16, 16), skinMat);

            head.position.set(0, 1.90, 0);

            group.add(head);



            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.50, 8), suitMat);

            armL.name = 'leftArm';

            armL.position.set(-0.44, 1.30, 0.12);

            armL.rotation.x = -0.80;

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.50, 8), suitMat);

            armR.name = 'rightArm';

            armR.position.set(0.44, 1.30, 0.12);

            armR.rotation.x = -0.80;

            group.add(armL, armR);



            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.18, 0.52, 0);

            const lPants = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.50, 8), suitMat);

            lPants.position.y = -0.24;

            const lShoe = new THREE.Mesh(createRoundedBoxGeometry(0.16, 0.11, 0.30, 0.03, 2), shoeMat);

            lShoe.position.set(0, -0.50, 0.05);

            leftLeg.add(lPants, lShoe);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.18, 0.52, 0);

            const rPants = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.50, 8), suitMat);

            rPants.position.y = -0.24;

            const rShoe = new THREE.Mesh(createRoundedBoxGeometry(0.16, 0.11, 0.30, 0.03, 2), shoeMat);

            rShoe.position.set(0, -0.50, 0.05);

            rightLeg.add(rPants, rShoe);



            group.add(leftLeg, rightLeg);

        }



        // =========================================================================

        // 11. WAYPOINT CORRIDOR PATHFINDING (NEVER WALK THROUGH FURNITURE!)

        // =========================================================================

        

        // =========================================================================

        // 10B. 3D MODELS CHO 10 NHÂN VẬT CỔ TÍCH VIỆT NAM (THƯ KÝ AI TIN TỨC)

        // Đầy đủ tai, mũi, mắt, miệng, lông mày, tóc và biểu tượng đặc trưng:

        // - Thạch Sanh: Cây rìu chiến khổng lồ đeo chéo sau lưng

        // - Mai An Tiêm: Đầu đội trái dưa hấu xanh sọc bổ góc đỏ tươi

        // - Thánh Gióng: Bụi tre ngà vàng óng sau lưng

        // - Chử Đồng Tử: Cây gậy thần và nón kỳ diệu

        // - Cô Tấm: Nón quai thao và chú chim vàng anh

        // - An Dương Vương: Mão vương triều và nỏ thần

        // =========================================================================

        buildFairyTaleCharacterMesh(group, charData) {

            const charKey = charData.key || 'thach_sanh';

            const rawApp = ((charData.appearance || (charData.secData && charData.secData.appearance) || '') + '').toLowerCase();



            // =========================================================================

            // A. PARSER PHÂN TÍCH ĐẶC ĐIỂM HÌNH DẠNG TỪ MÔ TẢ CỦA NGƯỜI DÙNG

            // =========================================================================



            // 1. Màu sắc trang phục chủ đạo (Torso)

            let torsoColor = (charKey === 'thach_sanh') ? 0x92400e : (charData.color || 0x0369a1);

            if (rawApp.includes('đỏ') || rawApp.includes('red')) torsoColor = 0xdc2626;

            else if (rawApp.includes('xanh lá') || rawApp.includes('xanh lục') || rawApp.includes('ngọc bích') || rawApp.includes('xanh non')) torsoColor = 0x16a34a;

            else if (rawApp.includes('navy') || rawApp.includes('xanh navy')) torsoColor = 0x1e3a8a;

            else if (rawApp.includes('xanh dương') || rawApp.includes('xanh lam') || rawApp.includes('xanh biển') || rawApp.includes('da trời') || rawApp.includes('blue')) torsoColor = 0x0284c7;

            else if (rawApp.includes('vàng') || rawApp.includes('yellow')) torsoColor = 0xeab308;

            else if (rawApp.includes('cam') || rawApp.includes('orange')) torsoColor = 0xea580c;

            else if (rawApp.includes('hồng') || rawApp.includes('pink') || rawApp.includes('cánh sen')) torsoColor = 0xec4899;

            else if (rawApp.includes('tím') || rawApp.includes('purple') || rawApp.includes('hoa cà')) torsoColor = 0x9333ea;

            else if (rawApp.includes('trắng') || rawApp.includes('white') || rawApp.includes('bạch')) torsoColor = 0xf8fafc;

            else if (rawApp.includes('đen') || rawApp.includes('black') || rawApp.includes('mun')) torsoColor = 0x1e293b;

            else if (rawApp.includes('nâu') || rawApp.includes('brown') || rawApp.includes('hạt dẻ')) torsoColor = 0x78350f;



            // 2. Kiểu trang phục

            const isVest = rawApp.includes('vest') || rawApp.includes('suit') || rawApp.includes('sơ mi') || rawApp.includes('công sở') || rawApp.includes('cà vạt') || rawApp.includes('tie');

            const isAoDai = rawApp.includes('áo dài') || rawApp.includes('ao dai');

            const isSkirt = rawApp.includes('váy') || rawApp.includes('đầm') || rawApp.includes('chân váy');



            // 3. Màu tóc

            let hairColor = 0x18181b;

            if (rawApp.includes('tóc vàng') || rawApp.includes('vàng kim') || rawApp.includes('blonde')) hairColor = 0xfacc15;

            else if (rawApp.includes('tóc nâu') || rawApp.includes('hạt dẻ')) hairColor = 0x78350f;

            else if (rawApp.includes('tóc đỏ') || rawApp.includes('hung đỏ')) hairColor = 0xb91c1c;

            else if (rawApp.includes('tóc bạc') || rawApp.includes('tóc trắng')) hairColor = 0xe2e8f0;

            else if (rawApp.includes('tóc hồng')) hairColor = 0xf472b6;

            else if (rawApp.includes('tóc xanh')) hairColor = 0x0ea5e9;



            // 4. Giới tính & kiểu tóc

            const isFemale = (charKey === 'co_tam' || charKey === 'cam') ||

                             rawApp.includes('nữ') || rawApp.includes('cô') || rawApp.includes('gái') ||

                             rawApp.includes('tiểu thư') || isAoDai || isSkirt || rawApp.includes('nơ');



            const isPonytail = rawApp.includes('đuôi ngựa') || rawApp.includes('buộc cao');

            const isTwinTail = rawApp.includes('hai bím') || rawApp.includes('hai chùm') || rawApp.includes('buộc 2 bên');

            const isShortHair = rawApp.includes('tóc ngắn') || rawApp.includes('bob') || rawApp.includes('tém') || rawApp.includes('undercut');



            // 5. Phụ kiện

            const hasGlasses = rawApp.includes('kính') || rawApp.includes('mắt kính') || rawApp.includes('kính cận') || rawApp.includes('kính tròn') || rawApp.includes('kính râm');

            const hasConicalHat = rawApp.includes('nón lá') || rawApp.includes('nón quai thao');

            const hasCrown = rawApp.includes('vương miện') || rawApp.includes('mão') || charKey === 'an_duong_vuong';

            const hasFlower = rawApp.includes('hoa') || rawApp.includes('cài hoa') || rawApp.includes('bông hoa');

            const hasBow = rawApp.includes('nơ') || rawApp.includes('cột nơ');

            const hasHeadphones = rawApp.includes('tai nghe') || rawApp.includes('headphone');

            const hasCap = rawApp.includes('mũ len') || rawApp.includes('nón kết') || rawApp.includes('mũ nồi') || rawApp.includes('beret');

            const hasBackpack = rawApp.includes('balo') || rawApp.includes('ba lô') || rawApp.includes('cặp');

            const hasCape = rawApp.includes('áo choàng') || rawApp.includes('choàng');

            const hasTablet = rawApp.includes('ipad') || rawApp.includes('máy tính bảng') || rawApp.includes('sổ') || rawApp.includes('tài liệu');



            // 6. Vóc dáng

            if (rawApp.includes('cao') || rawApp.includes('thanh mảnh') || rawApp.includes('thon thả')) {

                group.scale.set(0.96, 1.07, 0.96);

            } else if (rawApp.includes('nhỏ nhắn') || rawApp.includes('dễ thương') || rawApp.includes('nấm lùn') || rawApp.includes('thấp')) {

                group.scale.set(0.92, 0.90, 0.92);

            } else if (rawApp.includes('vạm vỡ') || rawApp.includes('cơ bắp') || rawApp.includes('mạnh mẽ') || rawApp.includes('đô con')) {

                group.scale.set(1.12, 1.03, 1.12);

            }



            // =========================================================================

            // B. VẬT LIỆU 3D CHUẨN

            // =========================================================================

            let skinTone = 0xffdfd0;

            if (rawApp.includes('da trắng') || rawApp.includes('trắng hồng')) skinTone = 0xfff0ea;

            else if (rawApp.includes('da ngăm') || rawApp.includes('bánh mật') || rawApp.includes('rám nắng')) skinTone = 0xc68a62;



            const skinMat = new THREE.MeshStandardMaterial({ color: skinTone, roughness: 0.6 });

            const hairMat = new THREE.MeshStandardMaterial({ color: hairColor, roughness: 0.45 });

            const eyeWhiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

            const pupilMat = new THREE.MeshBasicMaterial({ color: 0x09090b });

            const eyeCatchMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

            const eyebrowMat = new THREE.MeshBasicMaterial({ color: (hairColor === 0xfacc15) ? 0x854d0e : 0x27272a });

            const lipMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e });

            const torsoMat = new THREE.MeshStandardMaterial({ color: torsoColor, roughness: 0.65 });

            const shoeMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.5 });

            const goldMat = new THREE.MeshStandardMaterial({ color: 0xfacc15, metalness: 0.85, roughness: 0.25 });

            const woodMat = new THREE.MeshStandardMaterial({ color: 0x5c3317, roughness: 0.75 });

            const steelMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.2 });

            const brownClothMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.7 });



            // 1. TORSO (Thân trên)

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.40, 0.95, 14), torsoMat);

            torso.position.y = 1.0;

            torso.castShadow = true;

            group.add(torso);



            // Thắt lưng hoặc đai áo

            if (!isVest) {

                const beltColor = isAoDai ? 0xfacc15 : 0xd97706;

                const belt = new THREE.Mesh(new THREE.CylinderGeometry(0.455, 0.455, 0.12, 14), new THREE.MeshStandardMaterial({ color: beltColor }));

                belt.position.y = 0.82;

                group.add(belt);

            }



            // Trang phục Vest / Sơ mi công sở

            if (isVest) {

                const shirtMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 });

                const shirtPlate = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.08, 0.42, 8), shirtMat);

                shirtPlate.position.set(0, 1.22, 0.28);

                shirtPlate.rotation.x = 0.1;

                group.add(shirtPlate);



                const lapelMat = new THREE.MeshStandardMaterial({ color: torsoColor, roughness: 0.5 });

                for (let side of [-1, 1]) {

                    const lapel = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.40, 0.04), lapelMat);

                    lapel.position.set(side * 0.12, 1.20, 0.35);

                    lapel.rotation.z = -side * 0.22;

                    group.add(lapel);

                }



                const tieColor = (rawApp.includes('cà vạt vàng') || rawApp.includes('tie vàng')) ? 0xeab308 :

                                 (rawApp.includes('cà vạt xanh') || rawApp.includes('tie xanh')) ? 0x0284c7 :

                                 (rawApp.includes('cà vạt đen') || rawApp.includes('tie đen')) ? 0x09090b : 0xdc2626;

                const tieMat = new THREE.MeshStandardMaterial({ color: tieColor, roughness: 0.5 });

                const tieKnot = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 0.04), tieMat);

                tieKnot.position.set(0, 1.36, 0.35);

                const tieBody = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.36, 4), tieMat);

                tieBody.rotation.z = Math.PI;

                tieBody.position.set(0, 1.15, 0.35);

                group.add(tieKnot, tieBody);

            }



            // Tà áo dài (Áo Dài truyền thống)

            if (isAoDai) {

                const silkMat = new THREE.MeshStandardMaterial({ color: torsoColor, roughness: 0.4, side: THREE.DoubleSide });

                const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.08, 14), silkMat);

                collar.position.set(0, 1.50, 0);

                group.add(collar);



                const frontFlap = new THREE.Mesh(new THREE.PlaneGeometry(0.44, 0.95), silkMat);

                frontFlap.position.set(0, 0.55, 0.41);

                frontFlap.rotation.x = -0.05;



                const backFlap = new THREE.Mesh(new THREE.PlaneGeometry(0.44, 0.95), silkMat);

                backFlap.position.set(0, 0.55, -0.41);

                backFlap.rotation.x = 0.05;

                group.add(frontFlap, backFlap);

            }



            // 2. HEAD (Đầu)

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.44, 20, 20), skinMat);

            head.name = 'head';

            head.position.set(0, 1.90, 0);

            head.castShadow = true;

            group.add(head);



            // 3. TAI

            for (let side of [-1, 1]) {

                const ear = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 10), skinMat);

                ear.scale.set(0.4, 0.9, 0.7);

                ear.position.set(side * 0.43, 1.90, 0);

                group.add(ear);

            }



            // 4. MẮT & LÔNG MÀY

            for (let side of [-1, 1]) {

                const eyeWhite = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), eyeWhiteMat);

                eyeWhite.scale.set(1.0, 1.35, 0.35);

                eyeWhite.position.set(side * 0.14, 1.96, 0.40);



                const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.045, 10, 10), pupilMat);

                pupil.position.set(side * 0.14, 1.95, 0.43);



                const catchlight = new THREE.Mesh(new THREE.SphereGeometry(0.016, 6, 6), eyeCatchMat);

                catchlight.position.set(side * 0.125, 1.97, 0.445);



                const eyebrow = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.025, 0.02), eyebrowMat);

                eyebrow.rotation.z = side * 0.08;

                eyebrow.position.set(side * 0.14, 2.07, 0.41);



                group.add(eyeWhite, pupil, catchlight, eyebrow);

            }



            // 5. MŨI

            const nose = new THREE.Mesh(new THREE.ConeGeometry(0.04, 0.09, 8), skinMat);

            nose.rotation.x = Math.PI / 2;

            nose.position.set(0, 1.88, 0.45);

            group.add(nose);



            // 6. MIỆNG

            const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.065, 0.018, 6, 12, Math.PI), lipMat);

            mouth.rotation.x = Math.PI;

            mouth.position.set(0, 1.77, 0.42);

            group.add(mouth);



            // 7. MẮT KÍNH 3D (NẾU MÔ TẢ CÓ ĐEO KÍNH)

            if (hasGlasses) {

                const glassesGroup = new THREE.Group();

                const rimColor = (rawApp.includes('kính vàng') || rawApp.includes('gọng vàng')) ? 0xfacc15 :

                                 (rawApp.includes('kính bạc') || rawApp.includes('gọng bạc')) ? 0xe2e8f0 : 0x09090b;

                const rimMat = new THREE.MeshStandardMaterial({ color: rimColor, metalness: 0.8, roughness: 0.3 });

                const lensMat = new THREE.MeshStandardMaterial({ color: 0x93c5fd, roughness: 0.1, transparent: true, opacity: 0.45 });



                for (let side of [-1, 1]) {

                    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.08, 0.012, 8, 20), rimMat);

                    rim.position.set(side * 0.14, 1.96, 0.44);

                    const lens = new THREE.Mesh(new THREE.CircleGeometry(0.075, 16), lensMat);

                    lens.position.set(side * 0.14, 1.96, 0.44);

                    glassesGroup.add(rim, lens);



                    const temple = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.012, 0.36), rimMat);

                    temple.position.set(side * 0.22, 1.96, 0.26);

                    glassesGroup.add(temple);

                }

                const bridge = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.012, 0.012), rimMat);

                bridge.position.set(0, 1.97, 0.445);

                glassesGroup.add(bridge);



                group.add(glassesGroup);

            }



            // 8. MÁI TÓC (TUỲ BIẾN THEO MÔ TẢ)

            if (isFemale) {

                const hairTop = new THREE.Mesh(new THREE.SphereGeometry(0.46, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), hairMat);

                hairTop.position.set(0, 1.90, 0);

                group.add(hairTop);



                if (isPonytail) {

                    const ponyKnot = new THREE.Mesh(new THREE.SphereGeometry(0.12, 10, 10), hairMat);

                    ponyKnot.position.set(0, 2.05, -0.42);

                    const ponyTail = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.14, 0.70, 10), hairMat);

                    ponyTail.rotation.x = -0.35;

                    ponyTail.position.set(0, 1.70, -0.52);

                    const ponyRing = new THREE.Mesh(new THREE.TorusGeometry(0.09, 0.02, 6, 12), new THREE.MeshStandardMaterial({ color: 0xef4444 }));

                    ponyRing.position.set(0, 2.05, -0.40);

                    group.add(ponyKnot, ponyTail, ponyRing);

                } else if (isTwinTail) {

                    for (let side of [-1, 1]) {

                        const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.11, 0.65, 8), hairMat);

                        tail.position.set(side * 0.38, 1.65, -0.20);

                        tail.rotation.z = side * 0.20;

                        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.07, 0.02, 6, 12), new THREE.MeshStandardMaterial({ color: 0xec4899 }));

                        ring.position.set(side * 0.35, 1.98, -0.15);

                        group.add(tail, ring);

                    }

                } else if (isShortHair) {

                    const bobBack = new THREE.Mesh(new THREE.CylinderGeometry(0.44, 0.42, 0.50, 14), hairMat);

                    bobBack.position.set(0, 1.85, -0.10);

                    group.add(bobBack);

                } else {

                    const hairBack = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.35, 1.1, 14), hairMat);

                    hairBack.position.set(0, 1.72, -0.15);

                    group.add(hairBack);

                }

            } else {

                const hairCap = new THREE.Mesh(new THREE.SphereGeometry(0.46, 16, 16, 0, Math.PI * 2, 0, Math.PI / 1.8), hairMat);

                hairCap.position.set(0, 1.92, -0.04);

                group.add(hairCap);



                if (!isShortHair) {

                    const topknot = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 12), hairMat);

                    topknot.scale.set(1.0, 1.3, 0.9);

                    topknot.position.set(0, 2.42, -0.05);



                    const knotRing = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.03, 8, 16), new THREE.MeshStandardMaterial({ color: 0xdc2626 }));

                    knotRing.rotation.x = Math.PI / 2;

                    knotRing.position.set(0, 2.34, -0.05);

                    group.add(topknot, knotRing);

                }

            }



            // 9. CÁNH TAY

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.50, 8), torsoMat);

            armL.name = 'leftArm';

            armL.position.set(-0.44, 1.30, 0.12);

            armL.rotation.x = -0.80;



            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.09, 0.50, 8), torsoMat);

            armR.name = 'rightArm';

            armR.position.set(0.44, 1.30, 0.12);

            armR.rotation.x = -0.80;

            group.add(armL, armR);



            // 10. HAI CHÂN / VÁY

            if (isSkirt) {

                const skirtMat = new THREE.MeshStandardMaterial({ color: torsoColor, roughness: 0.6 });

                const skirt = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.65, 0.55, 14, 1, true), skirtMat);

                skirt.position.set(0, 0.65, 0);

                group.add(skirt);

            }



            const pantsColor = isVest ? torsoColor : brownClothMat.color;

            const pantsMat = new THREE.MeshStandardMaterial({ color: pantsColor, roughness: 0.7 });



            const leftLeg = new THREE.Group();

            leftLeg.name = 'leftLeg';

            leftLeg.position.set(-0.18, 0.52, 0);

            const lPants = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.50, 8), pantsMat);

            lPants.position.y = -0.24;

            const lShoe = new THREE.Mesh(createRoundedBoxGeometry(0.16, 0.11, 0.30, 0.03, 2), shoeMat);

            lShoe.position.set(0, -0.50, 0.05);

            leftLeg.add(lPants, lShoe);



            const rightLeg = new THREE.Group();

            rightLeg.name = 'rightLeg';

            rightLeg.position.set(0.18, 0.52, 0);

            const rPants = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.10, 0.50, 8), pantsMat);

            rPants.position.y = -0.24;

            const rShoe = new THREE.Mesh(createRoundedBoxGeometry(0.16, 0.11, 0.30, 0.03, 2), shoeMat);

            rShoe.position.set(0, -0.50, 0.05);

            rightLeg.add(rPants, rShoe);



            group.add(leftLeg, rightLeg);



            // =========================================================================

            // C. MŨ, NÓN & PHỤ KIỆN TÓC

            // =========================================================================

            if (hasConicalHat && !hasCrown) {

                const strawMat = new THREE.MeshStandardMaterial({ color: 0xdeb887, roughness: 0.85 });

                const nonLa = new THREE.Mesh(new THREE.ConeGeometry(0.56, 0.30, 24), strawMat);

                nonLa.position.set(0, 2.45, -0.02);

                nonLa.rotation.x = 0.12;

                group.add(nonLa);



                const strap = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.015, 6, 20), new THREE.MeshBasicMaterial({ color: 0xec4899 }));

                strap.rotation.x = Math.PI / 2;

                strap.position.set(0, 2.12, 0);

                group.add(strap);

            } else if (hasCrown) {

                const crown = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.20, 0.20, 8), goldMat);

                crown.position.set(0, 2.45, 0);

                for (let i = 0; i < 4; i++) {

                    const jewel = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 6), new THREE.MeshBasicMaterial({ color: 0xdc2626 }));

                    const angle = (i * Math.PI) / 2;

                    jewel.position.set(Math.cos(angle) * 0.25, 2.56, Math.sin(angle) * 0.25);

                    group.add(jewel);

                }

                group.add(crown);

            } else if (hasCap) {

                const capMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.6 });

                const cap = new THREE.Mesh(new THREE.SphereGeometry(0.47, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2.5), capMat);

                cap.position.set(0, 2.05, 0);

                group.add(cap);

            }



            if (hasFlower) {

                const flowerGroup = new THREE.Group();

                flowerGroup.position.set(0.36, 2.15, 0.15);

                const petalMat = new THREE.MeshStandardMaterial({ color: 0xf43f5e });

                for (let i = 0; i < 5; i++) {

                    const petal = new THREE.Mesh(new THREE.SphereGeometry(0.05, 6, 6), petalMat);

                    petal.scale.set(1.0, 0.3, 0.7);

                    const angle = (i * Math.PI * 2) / 5;

                    petal.position.set(Math.cos(angle) * 0.06, Math.sin(angle) * 0.06, 0);

                    flowerGroup.add(petal);

                }

                const center = new THREE.Mesh(new THREE.SphereGeometry(0.035, 6, 6), new THREE.MeshBasicMaterial({ color: 0xfacc15 }));

                flowerGroup.add(center);

                group.add(flowerGroup);

            }



            if (hasBow) {

                const bowGroup = new THREE.Group();

                bowGroup.position.set(0, 2.38, -0.10);

                const bowMat = new THREE.MeshStandardMaterial({ color: 0xef4444 });

                for (let side of [-1, 1]) {

                    const loop = new THREE.Mesh(new THREE.TorusGeometry(0.08, 0.025, 6, 12), bowMat);

                    loop.position.set(side * 0.09, 0, 0);

                    loop.rotation.y = side * 0.3;

                    bowGroup.add(loop);

                }

                const knot = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 6), bowMat);

                bowGroup.add(knot);

                group.add(bowGroup);

            }



            if (hasHeadphones) {

                const hpMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.5 });

                const headband = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.03, 8, 20, Math.PI), hpMat);

                headband.position.set(0, 1.95, 0);

                group.add(headband);

                for (let side of [-1, 1]) {

                    const earPad = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.06, 12), hpMat);

                    earPad.rotation.z = Math.PI / 2;

                    earPad.position.set(side * 0.46, 1.90, 0);

                    group.add(earPad);

                }

            }



            // =========================================================================

            // D. PHỤ KIỆN ĐẶC BIỆT

            // =========================================================================

            if (hasBackpack) {

                const packMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.7 });

                const backpack = new THREE.Mesh(createRoundedBoxGeometry(0.50, 0.60, 0.24, 0.06, 2), packMat);

                backpack.position.set(0, 1.10, -0.42);

                group.add(backpack);

            }



            if (hasCape) {

                const capeMat = new THREE.MeshStandardMaterial({ color: 0xb91c1c, roughness: 0.5, side: THREE.DoubleSide });

                const cape = new THREE.Mesh(new THREE.PlaneGeometry(0.70, 1.2), capeMat);

                cape.position.set(0, 0.90, -0.42);

                cape.rotation.x = 0.12;

                group.add(cape);

            }



            if (hasTablet) {

                const tabGroup = new THREE.Group();

                tabGroup.position.set(0.38, 0.95, 0.36);

                tabGroup.rotation.x = -0.5;

                const tabBody = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.34, 0.02), new THREE.MeshStandardMaterial({ color: 0x334155 }));

                const tabScreen = new THREE.Mesh(new THREE.PlaneGeometry(0.20, 0.30), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));

                tabScreen.position.z = 0.012;

                tabGroup.add(tabBody, tabScreen);

                group.add(tabGroup);

            }



            // =========================================================================

            // E. BIỂU TƯỢNG ĐẶC TRƯNG CỦA CÁC NHÂN VẬT CỔ TÍCH GỐC (NẾU PHÙ HỢP)

            // =========================================================================

            if (charKey === 'thach_sanh' && !isVest) {

                const axeGroup = new THREE.Group();

                axeGroup.position.set(0.18, 1.45, -0.42);

                axeGroup.rotation.z = -0.48;

                axeGroup.rotation.y = 0.20;



                const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.05, 1.5, 10), woodMat);

                handle.castShadow = true;

                axeGroup.add(handle);



                const mount = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.18, 8), goldMat);

                mount.position.y = 0.60;

                axeGroup.add(mount);



                const bladeShape = new THREE.Shape();

                bladeShape.moveTo(0, 0);

                bladeShape.quadraticCurveTo(0.45, 0.25, 0.55, 0.60);

                bladeShape.quadraticCurveTo(0.20, 0.40, 0, 0.30);

                bladeShape.closePath();

                const extrudeSettings = { depth: 0.04, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.02, bevelThickness: 0.02 };

                const bladeGeo = new THREE.ExtrudeGeometry(bladeShape, extrudeSettings);

                const blade = new THREE.Mesh(bladeGeo, steelMat);

                blade.position.set(0.02, 0.45, -0.02);

                blade.castShadow = true;

                axeGroup.add(blade);



                const spike = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.22, 6), steelMat);

                spike.rotation.z = -Math.PI / 2;

                spike.position.set(-0.16, 0.60, 0);

                axeGroup.add(spike);



                const strap = new THREE.Mesh(new THREE.TorusGeometry(0.48, 0.03, 6, 24), brownClothMat);

                strap.rotation.y = Math.PI / 2;

                strap.rotation.x = 0.65;

                strap.position.set(0, 1.05, 0);

                group.add(strap);



                group.add(axeGroup);



            } else if (charKey === 'mai_an_tiem' && !hasConicalHat && !hasCrown && !hasCap) {

                const melonGroup = new THREE.Group();

                melonGroup.position.set(0, 2.65, 0.05);

                melonGroup.rotation.z = 0.15;



                const melonMat = new THREE.MeshStandardMaterial({ color: 0x14532d, roughness: 0.45 });

                const melon = new THREE.Mesh(new THREE.SphereGeometry(0.26, 16, 16), melonMat);

                melon.scale.set(1.0, 1.15, 0.95);

                melon.castShadow = true;

                melonGroup.add(melon);



                const stripeMat = new THREE.MeshBasicMaterial({ color: 0x4ade80 });

                for (let a = 0; a < Math.PI * 2; a += Math.PI / 3) {

                    const stripe = new THREE.Mesh(new THREE.TorusGeometry(0.255, 0.016, 4, 16), stripeMat);

                    stripe.rotation.y = a;

                    stripe.scale.set(1.0, 1.15, 0.95);

                    melonGroup.add(stripe);

                }



                const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.10, 6), woodMat);

                stem.position.set(0, 0.32, 0);

                stem.rotation.z = 0.3;

                melonGroup.add(stem);



                const slice = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.04, 8, 1, false, 0, Math.PI / 1.5), new THREE.MeshStandardMaterial({ color: 0xef4444 }));

                slice.rotation.z = Math.PI / 2;

                slice.position.set(0.42, 1.50, 0.24);

                group.add(slice);



                group.add(melonGroup);



            } else if (charKey === 'thanh_giong' && !isVest) {

                const bambooGroup = new THREE.Group();

                bambooGroup.position.set(-0.20, 1.50, -0.38);

                bambooGroup.rotation.z = 0.35;



                const bambooMat = new THREE.MeshStandardMaterial({ color: 0xeab308, roughness: 0.4 });

                const jointMat = new THREE.MeshStandardMaterial({ color: 0xa16207 });

                const leafMat = new THREE.MeshStandardMaterial({ color: 0x22c55e });



                for (let b = 0; b < 3; b++) {

                    const bx = (b - 1) * 0.09;

                    const bz = (b % 2) * 0.05;

                    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.04, 1.7, 8), bambooMat);

                    stem.position.set(bx, 0, bz);

                    bambooGroup.add(stem);



                    for (let j = -0.6; j <= 0.7; j += 0.35) {

                        const joint = new THREE.Mesh(new THREE.TorusGeometry(0.042, 0.012, 6, 12), jointMat);

                        joint.rotation.x = Math.PI / 2;

                        joint.position.set(bx, j, bz);

                        bambooGroup.add(joint);

                    }



                    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.35, 4), leafMat);

                    leaf.rotation.z = (b - 1) * 0.5 + 0.3;

                    leaf.position.set(bx, 0.90, bz);

                    bambooGroup.add(leaf);

                }



                group.add(bambooGroup);



            } else if (charKey === 'an_duong_vuong') {

                const bowGroup = new THREE.Group();

                bowGroup.position.set(0, 1.35, -0.40);

                const bowArm = new THREE.Mesh(new THREE.TorusGeometry(0.40, 0.03, 6, 16, Math.PI), goldMat);

                bowArm.rotation.x = Math.PI / 2;

                const bowStock = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.04, 0.60, 6), woodMat);

                bowStock.rotation.x = Math.PI / 2;

                bowStock.position.z = 0.20;

                bowGroup.add(bowArm, bowStock);

                group.add(bowGroup);



            } else if (charKey === 'co_tam') {

                if (!hasConicalHat && !hasCrown) {

                    const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 0.05, 20), goldMat);

                    hat.rotation.x = 0.4;

                    hat.position.set(0, 1.35, -0.42);

                    group.add(hat);

                }



                const birdGroup = new THREE.Group();

                birdGroup.position.set(-0.46, 1.48, 0.10);

                const birdBody = new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 8), new THREE.MeshStandardMaterial({ color: 0xfacc15 }));

                birdBody.scale.set(1.0, 0.8, 1.3);

                const birdBeak = new THREE.Mesh(new THREE.ConeGeometry(0.02, 0.05, 4), new THREE.MeshBasicMaterial({ color: 0xf97316 }));

                birdBeak.rotation.x = Math.PI / 2;

                birdBeak.position.set(0, 0, 0.09);

                birdGroup.add(birdBody, birdBeak);

                group.add(birdGroup);



            } else if (!hasConicalHat && !hasCrown && !hasCap && !isVest && !isAoDai) {

                const defaultHat = new THREE.Mesh(new THREE.ConeGeometry(0.46, 0.24, 16), new THREE.MeshStandardMaterial({ color: 0xd4a373, roughness: 0.8 }));

                defaultHat.position.set(0, 2.45, 0);

                group.add(defaultHat);

            }

        }



        generateWalkPath(startPos, endPos) {

            const path = [];

            const sx = startPos.x, sz = startPos.z;

            const ex = endPos.x, ez = endPos.z;



            if (Math.hypot(ex - sx, ez - sz) < 0.25) {

                path.push(endPos.clone());

                return path;

            }



            function addPt(x, z) {

                if (path.length > 0) {

                    const last = path[path.length - 1];

                    if (Math.hypot(last.x - x, last.z - z) < 0.25) return;

                }

                path.push(new THREE.Vector3(x, 0.12, z));

            }



            // =========================================================================

            // ĐỊNH NGHĨA CÁC TUYẾN HÀNH LANG THÔNG THOÁNG TRONG PHÒNG (KHÔNG CÓ VẬT CẢN)

            // =========================================================================

            const AISLE_CENTRAL_Z = 1.8;       // Hành lang trung tâm Đông - Tây (Xuyên suốt từ X: -15 đến +14)

            const AISLE_NORTH_Z = -11.8;       // Hành lang phía Bắc (Trước mặt bàn thư ký & sau lưng dãy ghế Bắc bàn họp)

            const AISLE_SOUTH_CONF_Z = -5.5;   // Hành lang phía Nam bàn họp (Sau lưng dãy ghế Nam bàn họp)

            const CORRIDOR_EAST_X = 3.6;       // Hành lang Bắc - Nam giữa Bàn Giám Đốc và Bàn Họp

            const CORRIDOR_WEST_X = -4.5;      // Hành lang Bắc - Nam phía Tây Bàn Giám Đốc

            const CORRIDOR_FAR_WEST_X = -14.5; // Hành lang sát tường Tây (Bảng chiến lược, Vending bar, Zen garden)



            // Kiểm tra điểm có thuộc vùng ghế bàn họp không

            const isTargetNorthConf = (Math.abs(ez - (-10.05)) < 0.35 && ex >= 4.5);

            const isTargetSouthConf = (Math.abs(ez - (-6.95)) < 0.35 && ex >= 4.5);

            const isTargetHeadConf = (Math.abs(ez - (-8.5)) < 0.35 && Math.abs(ex - 4.75) < 0.7);

            const isTargetConf = isTargetNorthConf || isTargetSouthConf || isTargetHeadConf;



            const isStartNorthConf = (Math.abs(sz - (-10.05)) < 0.35 && sx >= 4.5);

            const isStartSouthConf = (Math.abs(sz - (-6.95)) < 0.35 && sx >= 4.5);

            const isStartHeadConf = (Math.abs(sz - (-8.5)) < 0.35 && Math.abs(sx - 4.75) < 0.7);

            const isStartConf = isStartNorthConf || isStartSouthConf || isStartHeadConf;



            // Kiểm tra vị trí ghế CEO đằng sau bàn làm việc (x: 0, z: -3.75)

            const isStartCeoChair = (Math.abs(sx) < 1.2 && sz <= -3.2 && sz >= -4.5);

            const isTargetCeoChair = (Math.abs(ex) < 1.2 && ez <= -3.2 && ez >= -4.5);



            // Kiểm tra điểm báo cáo trước bàn CEO (x: 0 hoặc quanh 0, z: -0.60)

            const isTargetCeoReport = (Math.abs(ex) < 1.5 && Math.abs(ez - (-0.60)) < 0.35);



            // 1. TRƯỜNG HỢP CEO BẮC NGUYỄN RỜI GHẾ LÀM VIỆC ĐI HỌP / SINH NHẬT / THUYẾT TRÌNH

            if (isStartCeoChair) {

                // Bước ngang qua hành lang CORRIDOR_EAST_X để không đi xuyên qua bàn làm việc của mình

                addPt(CORRIDOR_EAST_X, sz);

                if (isTargetConf) {

                    if (isTargetHeadConf) {

                        addPt(CORRIDOR_EAST_X, ez);

                    } else if (isTargetNorthConf) {

                        addPt(CORRIDOR_EAST_X, AISLE_NORTH_Z);

                        addPt(ex, AISLE_NORTH_Z);

                    } else {

                        addPt(CORRIDOR_EAST_X, AISLE_SOUTH_CONF_Z);

                        addPt(ex, AISLE_SOUTH_CONF_Z);

                    }

                    addPt(ex, ez);

                    return path;

                }

                addPt(CORRIDOR_EAST_X, AISLE_CENTRAL_Z);

                addPt(ex, AISLE_CENTRAL_Z);

                addPt(ex, ez);

                return path;

            }



            // 2. TRƯỜNG HỢP CEO BẮC NGUYỄN QUAY VỀ GHẾ LÀM VIỆC CỦA MÌNH

            if (isTargetCeoChair) {

                if (isStartConf) {

                    if (isStartHeadConf) {

                        addPt(CORRIDOR_EAST_X, sz);

                    } else if (isStartNorthConf) {

                        addPt(sx, AISLE_NORTH_Z);

                        addPt(CORRIDOR_EAST_X, AISLE_NORTH_Z);

                    } else {

                        addPt(sx, AISLE_SOUTH_CONF_Z);

                        addPt(CORRIDOR_EAST_X, AISLE_SOUTH_CONF_Z);

                    }

                    addPt(CORRIDOR_EAST_X, ez);

                    addPt(ex, ez);

                    return path;

                }

                addPt(sx, AISLE_CENTRAL_Z);

                addPt(CORRIDOR_EAST_X, AISLE_CENTRAL_Z);

                addPt(CORRIDOR_EAST_X, ez);

                addPt(ex, ez);

                return path;

            }



            // 3. TRƯỜNG HỢP RỜI KHỎI BÀN HỌP (RỜI DÃY GHẾ VỀ BÀN LÀM VIỆC)

            if (isStartConf) {

                if (isStartNorthConf) {

                    addPt(sx, AISLE_NORTH_Z);

                    addPt(CORRIDOR_EAST_X, AISLE_NORTH_Z);

                } else if (isStartSouthConf) {

                    addPt(sx, AISLE_SOUTH_CONF_Z);

                    addPt(CORRIDOR_EAST_X, AISLE_SOUTH_CONF_Z);

                } else if (isStartHeadConf) {

                    addPt(CORRIDOR_EAST_X, sz);

                }

                if (ez <= -12.0) {

                    addPt(CORRIDOR_EAST_X, AISLE_NORTH_Z);

                    addPt(ex, AISLE_NORTH_Z);

                    addPt(ex, ez);

                    return path;

                }

                addPt(CORRIDOR_EAST_X, AISLE_CENTRAL_Z);

                addPt(ex, AISLE_CENTRAL_Z);

                addPt(ex, ez);

                return path;

            }



            // 4. TRƯỜNG HỢP ĐI VÀO BÀN HỌP (TIẾP CẬN TỪ PHÍA SAU GHẾ, TUYỆT ĐỐI KHÔNG XUYÊN QUA BÀN)

            if (isTargetConf) {

                if (sz <= -12.0) {

                    addPt(sx, AISLE_NORTH_Z);

                    addPt(CORRIDOR_EAST_X, AISLE_NORTH_Z);

                } else if (sz >= 2.5) {

                    addPt(sx, AISLE_CENTRAL_Z);

                    addPt(CORRIDOR_EAST_X, AISLE_CENTRAL_Z);

                } else {

                    addPt(CORRIDOR_EAST_X, sz);

                }



                if (isTargetNorthConf) {

                    addPt(CORRIDOR_EAST_X, AISLE_NORTH_Z);

                    addPt(ex, AISLE_NORTH_Z);

                    addPt(ex, ez);

                } else if (isTargetSouthConf) {

                    addPt(CORRIDOR_EAST_X, AISLE_SOUTH_CONF_Z);

                    addPt(ex, AISLE_SOUTH_CONF_Z);

                    addPt(ex, ez);

                } else if (isTargetHeadConf) {

                    addPt(CORRIDOR_EAST_X, ez);

                    addPt(ex, ez);

                }

                return path;

            }



            // 5. TRƯỜNG HỢP DI CHUYỂN GIỮA VÙNG THƯ KÝ (Z <= -12.0) VÀ PHÍA NAM

            // TUYỆT ĐỐI ĐI VÒNG QUA HÀNH LANG, KHÔNG BAO GIỜ ĐI XUYÊN BÀN GIÁM ĐỐC HAY BÀN HỌP!

            if (sz <= -12.0 || ez <= -12.0) {

                const useCorr = (sx < 0 || ex < 0) ? CORRIDOR_WEST_X : CORRIDOR_EAST_X;

                if (sz <= -12.0) {

                    addPt(sx, AISLE_NORTH_Z);

                    addPt(useCorr, AISLE_NORTH_Z);

                    addPt(useCorr, AISLE_CENTRAL_Z);

                    if (isTargetCeoReport) {

                        addPt(0, AISLE_CENTRAL_Z);

                        addPt(0, ez);

                        return path;

                    }

                    addPt(ex, AISLE_CENTRAL_Z);

                    addPt(ex, ez);

                    return path;

                } else {

                    if (Math.abs(sz - AISLE_CENTRAL_Z) > 0.8) {

                        addPt(sx, AISLE_CENTRAL_Z);

                    }

                    addPt(useCorr, AISLE_CENTRAL_Z);

                    addPt(useCorr, AISLE_NORTH_Z);

                    addPt(ex, AISLE_NORTH_Z);

                    addPt(ex, ez);

                    return path;

                }

            }



            // 6. TRƯỜNG HỢP ĐI BÁO CÁO CEO (DỪNG TRƯỚC BÀN TẠI Z = -0.60, KHÔNG XUYÊN VÀO BÀN)

            if (isTargetCeoReport) {

                if (Math.abs(sz - AISLE_CENTRAL_Z) > 0.6) {

                    addPt(sx, AISLE_CENTRAL_Z);

                }

                addPt(0, AISLE_CENTRAL_Z);

                addPt(0, ez);

                return path;

            }



            // 7. TRƯỜNG HỢP ĐI SANG TƯỜNG TRÁI (BẢNG CHIẾN LƯỢC, ZEN GARDEN, CÔNG TẮC ĐÈN)

            if (ex <= -13.5) {

                addPt(sx, AISLE_CENTRAL_Z);

                addPt(CORRIDOR_FAR_WEST_X, AISLE_CENTRAL_Z);

                addPt(CORRIDOR_FAR_WEST_X, ez);

                addPt(ex, ez);

                return path;

            }

            if (sx <= -13.5) {

                addPt(CORRIDOR_FAR_WEST_X, sz);

                addPt(CORRIDOR_FAR_WEST_X, AISLE_CENTRAL_Z);

                addPt(ex, AISLE_CENTRAL_Z);

                addPt(ex, ez);

                return path;

            }



            // 8. ĐIỀU HƯỚNG TIÊU CHUẨN THEO HÀNH LANG TRUNG TÂM

            if (Math.abs(sz - AISLE_CENTRAL_Z) > 0.8) {

                addPt(sx, AISLE_CENTRAL_Z);

            }

            if (Math.abs(sx - ex) > 0.5) {

                addPt(ex, AISLE_CENTRAL_Z);

            }

            addPt(ex, ez);



            return path;

        }



        // =========================================================================

        // 12. LIGHT SWITCH & PHAN ĐINH TÙNG BIRTHDAY PARTY CONTROLLER

        // =========================================================================

                toggleLightsAndBirthday() {

            if (this.isBirthdayActive) {

                this.endBirthdayParty();

                return;

            }



            // Kích hoạt bài hát sinh nhật ngay lập tức trong sự kiện click của người dùng (tránh bị chặn bởi browser policy)

            if (this.audioPlayer) {

                this.audioPlayer.startBirthdaySong();

            }



            this.isBirthdayActive = true;

            this.birthdayTimer = 0;

            this.birthdayStage = 'celebrating';



            // Giảm 80% ánh sáng trong phòng làm việc

            this.targetLightFactor = 0.20;

            if (this.lightSwitchLever) {

                this.lightSwitchLever.rotation.x = 0.4;

            }



            const allCandidates = [

                { name: 'CIO Bắc Nguyễn', isCEO: true },

                ...this.characters.map(c => ({ name: c.characterName, id: c.id, mesh: c.mesh }))

            ];

            this.birthdayStar = allCandidates[Math.floor(Math.random() * allCandidates.length)];



            // Thắp nến và mang bánh kem sinh nhật ra bàn họp

            if (!this.birthdayCakeObj) {

                const { group: cakeGroup, candleLight } = buildBirthdayCake();

                cakeGroup.position.set(9.5, 0.85, -8.5);

                this.scene.add(cakeGroup);

                this.birthdayCakeObj = cakeGroup;

                this.candleLight = candleLight;

            }



            // Đội nón sinh nhật và giăng banner chúc mừng

            if (this.birthdayStar) {

                if (!this.partyHat) {

                    this.partyHat = buildPartyHat();

                }

                if (this.birthdayStar.isCEO && this.nobita) {

                    this.nobita.character.add(this.partyHat);

                    this.partyHat.position.set(0, 2.5, 0);

                } else if (this.birthdayStar.mesh) {

                    this.birthdayStar.mesh.add(this.partyHat);

                    this.partyHat.position.set(0, 2.5, 0);

                }



                if (!this.celebrationBanner) {

                    this.celebrationBanner = createCelebrationBanner(this.birthdayStar.name);

                    this.celebrationBanner.position.set(9.5, 3.8, -8.5);

                    this.scene.add(this.celebrationBanner);

                }

            }



            // CEO Bắc Nguyễn di chuyển đến ghế chủ tọa đầu bàn họp để chúc mừng (4.75, 0.12, -8.5)

            if (this.nobita) {

                this.nobita.state = 'walking_to_party';

                this.nobita.isSitting = false;

                const partyCEOSeat = new THREE.Vector3(4.75, 0.12, -8.5);

                this.nobita.walkWaypoints = this.generateWalkPath(this.nobita.character.position, partyCEOSeat);

            }



            // YÊU CẦU 1: 12 GHẾ BÀN HỌP (6 ghế dãy Bắc x = 5.75..13.25, 6 ghế dãy Nam x = 5.75..13.25)

            const meetingSideA = [

                new THREE.Vector3(5.75, 0.10, -10.05),

                new THREE.Vector3(7.25, 0.10, -10.05),

                new THREE.Vector3(8.75, 0.10, -10.05),

                new THREE.Vector3(10.25, 0.10, -10.05),

                new THREE.Vector3(11.75, 0.10, -10.05),

                new THREE.Vector3(13.25, 0.10, -10.05)

            ];

            const meetingSideB = [

                new THREE.Vector3(5.75, 0.10, -6.95),

                new THREE.Vector3(7.25, 0.10, -6.95),

                new THREE.Vector3(8.75, 0.10, -6.95),

                new THREE.Vector3(10.25, 0.10, -6.95),

                new THREE.Vector3(11.75, 0.10, -6.95),

                new THREE.Vector3(13.25, 0.10, -6.95)

            ];



            for (let i = 0; i < this.characters.length; i++) {

                const asst = this.characters[i];

                asst.state = 'birthday_party';

                asst.stateTime = 0;

                if (asst.lightbulb) asst.lightbulb.visible = false;

                const seat = (i % 2 === 0) ? meetingSideA[Math.floor(i / 2) % 6] : meetingSideB[Math.floor(i / 2) % 6];

                asst.targetPos.copy(seat);

                asst.walkPath = this.generateWalkPath(asst.mesh.position, seat);

            }



            this.updatePartyUI(true, 30);

        }



        endBirthdayParty() {

            this.isBirthdayActive = false;

            this.birthdayStage = 'idle';

            this.birthdayTimer = 0;



            this.targetLightFactor = 1.0;



            if (this.lightSwitchLever) {

                this.lightSwitchLever.rotation.x = 0;

            }



            if (this.birthdayCakeObj) {

                this.scene.remove(this.birthdayCakeObj);

                this.birthdayCakeObj = null;

                this.candleLight = null;

            }

            if (this.partyHat && this.partyHat.parent) {

                this.partyHat.parent.remove(this.partyHat);

                this.partyHat = null;

            }

            if (this.celebrationBanner && this.celebrationBanner.parent) {

                this.celebrationBanner.parent.remove(this.celebrationBanner);

                this.celebrationBanner = null;

            }



            this.audioPlayer.stopBirthdaySong();



            if (this.nobita) {

                this.nobita.state = 'returning_from_party';

                this.nobita.stateTime = 0;

                this.nobita.isSitting = false;

                this.nobita.walkWaypoints = this.generateWalkPath(this.nobita.character.position, this.nobita.homePos);

            }



            for (const asst of this.characters) {

                asst.state = 'returning';

                asst.stateTime = 0;

                asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

            }



            this.updatePartyUI(false);

        }



        updatePartyUI(active, remainingSec = 0) {

            const btn = document.getElementById('officeLightSwitchBtn');

            const icon = document.getElementById('officeLightIcon');

            const label = document.getElementById('officeLightLabel');

            if (!btn || !label) return;



            if (active) {

                btn.className = 'px-2.5 py-1 text-xs font-semibold rounded-lg bg-amber-500 text-white border border-amber-600 hover:bg-amber-600 transition flex items-center space-x-1.5 shadow-md animate-pulse';

                if (icon) icon.className = 'fa-solid fa-cake-candles text-white text-[11px]';

                label.textContent = `Bật đèn (${remainingSec}s 🎂)`;

            } else {

                btn.className = 'px-2.5 py-1 text-xs font-semibold rounded-lg bg-amber-50 text-amber-700 border border-amber-300 hover:bg-amber-100 transition flex items-center space-x-1.5 shadow-2xs';

                if (icon) icon.className = 'fa-solid fa-lightbulb text-amber-500 text-[11px]';

                label.textContent = 'Tắt đèn / Sinh nhật 🎂';

            }

        }



        // =========================================================================

        // 13. ANIMATION LOOP & BEHAVIOR SYSTEM

        // =========================================================================

        animate() {

            this.animationFrameId = requestAnimationFrame(() => this.animate());

            try {



            const rawDelta = this.clock.getDelta();

            const delta = Math.min(rawDelta, 0.05); // Cap delta to max 50ms (20fps minimum) to prevent overshoot or teleportation!

            const elapsed = this.clock.getElapsedTime();



            // Smooth Lighting Dimming (Drops by 80%)

            this.currentLightFactor += (this.targetLightFactor - this.currentLightFactor) * Math.min(1.0, delta * 3.5);

            if (this.ambientLight) this.ambientLight.intensity = 0.75 * this.currentLightFactor;

            if (this.sunLight) this.sunLight.intensity = 0.95 * this.currentLightFactor;

            if (this.deskLight) this.deskLight.intensity = 0.40 * this.currentLightFactor;

            if (this.meetingLight) this.meetingLight.intensity = 0.65 * this.currentLightFactor;

            if (this.fillLight) this.fillLight.intensity = 0.35 * this.currentLightFactor;

            if (this.wallSconceLights) {

                for (let sl of this.wallSconceLights) {

                    if (sl) sl.intensity = 0.42 * this.currentLightFactor;

                }

            }



            // Birthday Candle Flame Flicker

            if (this.candleLight) {

                this.candleLight.intensity = 2.4 + Math.sin(elapsed * 18) * 0.35 + Math.cos(elapsed * 27) * 0.25;

            }



            // Birthday Countdown (chờ hết đúng thời lượng bài hát Phan Đinh Tùng)

            if (this.isBirthdayActive && this.birthdayStage === 'celebrating') {

                const bAudio = (this.audioPlayer && this.audioPlayer.birthdayAudio);

                const isAudioPlaying = bAudio && !bAudio.paused && !bAudio.ended && bAudio.currentTime > 0;

                const audioDuration = (bAudio && bAudio.duration > 5) ? bAudio.duration : 30.5;



                if (isAudioPlaying) {

                    this.birthdayTimer = bAudio.currentTime;

                } else {

                    this.birthdayTimer += delta;

                }



                const rem = Math.max(0, Math.ceil(audioDuration - this.birthdayTimer));

                this.updatePartyUI(true, rem);



                // YÊU CẦU: Phải hết nhạc sinh nhật thì CIO và các nhân vật mới quay về chỗ ngồi!

                // Chỉ kết thúc khi thẻ Audio báo 'ended' hoặc khi quá thời gian kèm 2.5 giây đệm dự phòng

                if (bAudio && bAudio.ended) {

                    this.endBirthdayParty();

                } else if (!isAudioPlaying && this.birthdayTimer >= (audioDuration + 2.5)) {

                    this.endBirthdayParty();

                }

            }



            // Autonomous Meeting Timer

            this.meetingTimer += delta;

            if (this.meetingTimer > 360 && !this.isMeetingActive && !this.isBirthdayActive && this.characters.length > 0) {

                this.startMeeting();

            }



            // Update CEO Nobita

            this.updateNobitaBehavior(delta, elapsed);



            // Spin Take-copters

            for (const prop of this.takeCopterPropellers) {

                prop.rotation.y += delta * 18;

            }



            // Update Assistants

            this.updateAssistantBehaviors(delta, elapsed);



            // HARD SAFETY BOUNDARY & NAN GUARD: Keep all characters strictly inside the room forever

            if (this.nobita && this.nobita.character) {

                const np = this.nobita.character.position;

                if (isNaN(np.x) || isNaN(np.z) || Math.abs(np.x) > 15.5 || Math.abs(np.z) > 15.5) {

                    np.copy(this.nobita.homePos);

                    this.nobita.character.rotation.y = this.nobita.homeRot;

                    this.nobita.character.position.y = 0.12;

                    this.nobita.state = 'working';

                    this.nobita.stateTime = 0;

                    this.nobita.isSitting = true;

                    if (this.nobita.leftLeg) this.nobita.leftLeg.rotation.x = -Math.PI / 2.2;

                    if (this.nobita.rightLeg) this.nobita.rightLeg.rotation.x = -Math.PI / 2.2;

                    this.nobita.walkWaypoints = [];

                }

            }

            if (this.characters && this.characters.length > 0) {

                for (const asst of this.characters) {

                    if (asst.mesh) {

                        const ap = asst.mesh.position;

                        if (isNaN(ap.x) || isNaN(ap.z) || Math.abs(ap.x) > 15.5 || Math.abs(ap.z) > 15.5) {

                            ap.copy(asst.homePos);

                            asst.mesh.rotation.y = asst.homeRot;

                            asst.mesh.position.y = 0.10;

                            asst.state = 'working';

                            asst.stateTime = 0;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = -Math.PI / 2.2;

                                asst.rightLeg.rotation.x = -Math.PI / 2.2;

                            }

                            asst.walkPath = [];

                        }

                    }

                }

            }



            if (this.renderer && this.scene && this.camera) {

                this.updateVideoOverlayPosition();

            this.renderer.render(this.scene, this.camera);

            }

            } catch (err) {

                console.warn("DoraemonOffice 3D render loop guard:", err);

            }

        }



        updateNobitaBehavior(delta, elapsed) {

            if (!this.nobita) return;

            const n = this.nobita;

            n.stateTime += delta;



            // YÊU CẦU 1: ĐỘ MỜ BẢNG TÊN CIO BẮC NGUYỄN KHI VÀO / RA BÀN HỌP

            if (n.badgeSprite && n.badgeSprite.material) {

                let targetOpacity = 1.0;

                const headSeat = new THREE.Vector3(4.75, 0.12, -8.5);

                if (this.isMeetingActive || this.isBirthdayActive || n.state === 'meeting' || n.state === 'walking_to_meeting' || n.state === 'walking_to_party' || n.state === 'celebrating_party') {

                    if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                        const dHome = n.character.position.distanceTo(n.homePos);

                        const dSeat = n.character.position.distanceTo(headSeat);

                        const total = dHome + dSeat;

                        const prog = total > 0.1 ? Math.min(1.0, Math.max(0.0, dHome / total)) : 1.0;

                        targetOpacity = 1.0 - prog * 0.90; // Từ từ giảm xuống 10%

                    } else {

                        targetOpacity = 0.10; // Ngồi họp: 10%

                    }

                } else if (n.state === 'returning_from_party' || n.state === 'returning_from_meeting') {

                    const dHome = n.character.position.distanceTo(n.homePos);

                    const dSeat = n.character.position.distanceTo(headSeat);

                    const total = dHome + dSeat;

                    const prog = total > 0.1 ? Math.min(1.0, Math.max(0.0, dSeat / total)) : 1.0;

                    targetOpacity = 0.10 + prog * 0.90; // Từ từ tăng lên 100%

                } else {

                    targetOpacity = 1.0;

                }

                n.badgeSprite.material.opacity += (targetOpacity - n.badgeSprite.material.opacity) * Math.min(1.0, delta * 4.0);

            }



            // UNIVERSAL SAFETY WATCHDOG FOR CIO NOBITA: If roaming/moving/meeting for > 25s, force reset to desk

            // CHÚ Ý QUAN TRỌNG: KHÔNG ĐƯỢC RESET KHI ĐANG TRONG SINH NHẬT (this.isBirthdayActive) HOẶC HỌP (this.isMeetingActive)!

            // Phải chờ hết nhạc sinh nhật thì CIO mới cùng các trợ lý quay về chỗ ngồi!

            if (n.state !== 'working' && !this.isBirthdayActive && !this.isMeetingActive && !this.isDancingActive && n.stateTime > 25.0) {

                n.character.position.copy(n.homePos);

                n.character.rotation.y = n.homeRot;

                n.character.position.y = 0.12;

                n.state = 'working';

                n.stateTime = 0;

                n.isSitting = true;

                if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                n.walkWaypoints = [];

            }



            // YEU CAU 4: DANCE PARTY BEHAVIOR KHI PHAT NHAC YOUTUBE

            if (this.isDancingActive) {

                if (n.badgeSprite) n.badgeSprite.visible = false;



                if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                    const nextTarget = n.walkWaypoints[0];

                    const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                    diff.y = 0;

                    const dist = diff.length();

                    const step = 5.2 * delta;

                    if (dist > 0.32 && dist > step) {

                        diff.normalize();

                        n.character.position.addScaledVector(diff, step);

                        n.character.rotation.y = Math.atan2(diff.x, diff.z);

                        n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.14;

                        if (n.leftLeg && n.rightLeg) {

                            n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                        }

                        if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                        if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                    } else {

                        n.walkWaypoints.shift();

                    }

                } else {

                    // Da den giua phong: Cap 1 (CIO Bac Nguyen & Shizuka) nam tay nhau khieu vu nhip nhang (YEU CAU 1)

                    const pair1Center = new THREE.Vector3(-1.8, 0, 3.0);

                    const pairCycle = elapsed % 15.0;

                    let spinAngle = 0;

                    if (pairCycle > 11.5) {

                        const spinProg = (pairCycle - 11.5) / 3.5;

                        const smooth = (1 - Math.cos(spinProg * Math.PI)) / 2;

                        spinAngle = smooth * Math.PI * 2;

                    } else {

                        spinAngle = Math.sin(elapsed * 1.5) * 0.6; // Dong dua qua lai nhip nhang, lau lau moi xoay 1 vong

                    }

                    const r = 0.62;



                    const posX = pair1Center.x + Math.cos(spinAngle) * r;

                    const posZ = pair1Center.z + Math.sin(spinAngle) * r;

                    const bounceY = 0.12 + Math.abs(Math.sin(elapsed * 6.5)) * 0.16;



                    n.character.position.set(posX, bounceY, posZ);

                    n.character.rotation.y = spinAngle + Math.PI; // Huong ve ban nhay Shizuka

                    n.character.rotation.z = Math.sin(elapsed * 6.5) * 0.12;



                    // Hai tay vuon ra phia truoc nam tay ban nhay

                    if (n.leftArm) {

                        n.leftArm.rotation.x = -1.25;

                        n.leftArm.rotation.z = 0.25;

                    }

                    if (n.rightArm) {

                        n.rightArm.rotation.x = -1.25;

                        n.rightArm.rotation.z = -0.25;

                    }

                    // Chan buoc nhịp nhay

                    if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 7.0) * 0.45;

                    if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 7.0) * 0.45;

                }

                return;

            }



            // BIRTHDAY PARTY BEHAVIOR

            if (this.isBirthdayActive) {

                // Đảm bảo CIO luôn ở trạng thái sinh nhật, không bao giờ quay về bàn khi nhạc chưa dứt!

                if (n.state !== 'walking_to_party' && n.state !== 'celebrating_party' && n.state !== 'walking_to_switch' && n.state !== 'flipping_switch') {

                    n.state = 'celebrating_party';

                    n.stateTime = 0;

                    n.character.position.set(4.75, 0.12, -8.5);

                    n.character.rotation.y = Math.PI / 2;

                    if (n.leftLeg) n.leftLeg.rotation.x = 0;

                    if (n.rightLeg) n.rightLeg.rotation.x = 0;

                }



                if (n.state === 'walking_to_switch') {

                    if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                        const nextTarget = n.walkWaypoints[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = 2.4 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                    } else {

                        n.state = 'flipping_switch';

                        n.stateTime = 0;

                        n.character.rotation.y = -Math.PI / 2;

                        if (n.rightArm) n.rightArm.rotation.x = -1.5;

                        this.audioPlayer.playSwitchClick();



                        if (this.lightSwitchLever) this.lightSwitchLever.rotation.x = 0.4;

                        this.targetLightFactor = 0.20;

                        this.audioPlayer.startBirthdaySong();

                        this.birthdayStage = 'gathering';



                        if (!this.birthdayCakeObj) {

                            const { group: cakeGroup, candleLight } = buildBirthdayCake();

                            cakeGroup.position.set(9.5, 0.85, -8.5);

                            this.scene.add(cakeGroup);

                            this.birthdayCakeObj = cakeGroup;

                            this.candleLight = candleLight;

                        }



                        if (this.birthdayStar) {

                            if (!this.partyHat) {

                                this.partyHat = buildPartyHat();

                            }

                            if (this.birthdayStar.isCEO) {

                                n.character.add(this.partyHat);

                                this.partyHat.position.set(0, 2.5, 0);

                            } else if (this.birthdayStar.mesh) {

                                this.birthdayStar.mesh.add(this.partyHat);

                                this.partyHat.position.set(0, 2.5, 0);

                            }



                            if (!this.celebrationBanner) {

                                this.celebrationBanner = createCelebrationBanner(this.birthdayStar.name);

                                this.celebrationBanner.position.set(9.5, 3.8, -8.5);

                                this.scene.add(this.celebrationBanner);

                            }

                        }



                        setTimeout(() => {

                            n.state = 'walking_to_party';

                            const partyCEOSeat = new THREE.Vector3(4.75, 0.12, -8.5);

                            n.walkWaypoints = this.generateWalkPath(n.character.position, partyCEOSeat);

                            this.birthdayStage = 'celebrating';

                            this.birthdayTimer = 0;

                        }, 1200);

                    }

                    return;

                } else if (n.state === 'walking_to_party') {

                    if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                        const nextTarget = n.walkWaypoints[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = 2.4 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                    } else {

                        n.state = 'celebrating_party';

                        n.stateTime = 0;

                        n.character.position.set(4.75, 0.12, -8.5);

                        n.character.rotation.y = Math.PI / 2;

                        if (n.leftLeg) n.leftLeg.rotation.x = 0;

                        if (n.rightLeg) n.rightLeg.rotation.x = 0;

                    }

                    return;

                } else if (n.state === 'celebrating_party') {

                    if (n.leftArm) n.leftArm.rotation.x = -1.1 + Math.sin(elapsed * 12) * 0.25;

                    if (n.rightArm) n.rightArm.rotation.x = -1.1 + Math.cos(elapsed * 12) * 0.25;

                    if (n.head) n.head.rotation.y = Math.sin(elapsed * 3) * 0.2;

                    return;

                }

            }



            // SAFETY: Khi sinh nhat ket thuc, neu CEO con o bat ky trang thai party nao thi quay ve ban

            if (!this.isBirthdayActive && (n.state === 'walking_to_switch' || n.state === 'flipping_switch' || n.state === 'walking_to_party' || n.state === 'celebrating_party')) {

                n.state = 'returning_from_party';

                n.stateTime = 0;

                n.isSitting = false;

                n.walkWaypoints = this.generateWalkPath(n.character.position, n.homePos);

            }



            // CEO BAC NGUYEN DI CHUYYEN VE BAN LAM VIEC CUA MINH SAU SINH NHAT

            if (n.state === 'returning_from_party') {

                if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                    const nextTarget = n.walkWaypoints[0];

                    const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                    diff.y = 0;

                    const dist = diff.length();

                        // Tốc độ bước chân 1.35 * delta nhịp nhàng, mất khoảng 7-8 giây về đến bàn, cùng lúc với các trợ lý khác!

                        const step = 1.35 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                } else {

                    // Tro ve ghe giam doc, ngoi ngay ngan lam viec

                    n.character.position.copy(n.homePos);

                    n.character.rotation.y = n.homeRot;

                    n.character.position.y = 0.12;

                    n.state = 'working';

                    n.stateTime = 0;

                    n.isSitting = true;

                    if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                    if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                }

                // Watchdog an toan

                if (n.stateTime > 16.0) {

                    n.character.position.copy(n.homePos);

                    n.character.rotation.y = n.homeRot;

                    n.character.position.y = 0.12;

                    n.state = 'working';

                    n.stateTime = 0;

                    n.isSitting = true;

                    if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                    if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                }

                return;

            }



            // MEETING MODE BEHAVIOR (CEO stands up, walks to head chair, sits, and chairs the meeting)

            if (this.isMeetingActive) {

                if (n.state === 'working' || n.state === 'stretching' || n.state === 'walking_to_wb' || n.state === 'presenting' || n.state === 'returning_from_wb') {

                    n.state = 'walking_to_meeting';

                    n.stateTime = 0;

                    n.isSitting = false;

                    const ceoMeetingSeat = new THREE.Vector3(4.75, 0.12, -8.5);

                    n.walkWaypoints = this.generateWalkPath(n.character.position, ceoMeetingSeat);

                }



                if (n.state === 'walking_to_meeting') {

                    if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                        const nextTarget = n.walkWaypoints[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = 2.4 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                    } else {

                        // Seated into head conference chair!

                        n.state = 'meeting';

                        n.stateTime = 0;

                        n.character.position.set(4.75, 0.12, -8.5);

                        n.character.rotation.y = Math.PI / 2;

                        n.isSitting = true;

                        if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                        if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                    }

                    return;

                }



                if (n.state === 'meeting') {

                    n.character.position.set(4.75, 0.12, -8.5);

                    n.character.rotation.y = Math.PI / 2;

                    n.isSitting = true;

                    if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                    if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                    if (n.leftArm) n.leftArm.rotation.x = -0.80 + Math.sin(elapsed * 4) * 0.15;

                    if (n.rightArm) n.rightArm.rotation.x = -0.80 + Math.cos(elapsed * 4) * 0.18;

                    if (n.head) n.head.rotation.y = Math.sin(elapsed * 1.5) * 0.25;

                    return;

                }

            }



            // MEETING ENDED -> RETURN TO EXECUTIVE DESK

            if (n.state === 'meeting' || n.state === 'walking_to_meeting') {

                n.state = 'returning_from_meeting';

                n.stateTime = 0;

                n.isSitting = false;

                n.walkWaypoints = this.generateWalkPath(n.character.position, n.homePos);

            }



            if (n.state === 'returning_from_meeting') {

                if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                    const nextTarget = n.walkWaypoints[0];

                    const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                    diff.y = 0;

                    const dist = diff.length();

                        const step = 2.4 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                } else {

                    // Back seated in executive chair!

                    n.character.position.copy(n.homePos);

                    n.character.rotation.y = n.homeRot;

                    n.state = 'working';

                    n.stateTime = 0;

                    n.isSitting = true;

                    if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                    if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                }

                return;

            }



            // NORMAL WORK & ROUTINE

            if (n.state === 'working') {

                if (n.leftArm) {

                    n.leftArm.rotation.x = -0.75 + Math.sin(elapsed * 5) * 0.05;

                    n.leftArm.rotation.y = -0.22 + Math.cos(elapsed * 4) * 0.03;

                    n.leftArm.rotation.z = -0.10;

                }

                if (n.rightArm) {

                    n.rightArm.rotation.x = -0.75 + Math.cos(elapsed * 5) * 0.05;

                    n.rightArm.rotation.y = 0.22 - Math.sin(elapsed * 4) * 0.03;

                    n.rightArm.rotation.z = 0.10;

                }

                if (n.head) n.head.rotation.y = Math.sin(elapsed * 0.8) * 0.12;



                if (n.stateTime > 28 && n.stateTime < 54) {

                    n.state = 'stretching';

                    n.stateTime = 0;

                } else if (n.stateTime >= 54) {

                    n.state = 'walking_to_wb';

                    n.stateTime = 0;

                    n.isSitting = false;

                    const wbTarget = new THREE.Vector3(-12.5, 0.12, 7.5);

                    n.walkWaypoints = this.generateWalkPath(n.character.position, wbTarget);

                }

            } else if (n.state === 'stretching') {

                if (n.leftArm) {

                    n.leftArm.rotation.x = -2.2;

                    n.leftArm.rotation.z = -0.45 + Math.sin(elapsed * 4) * 0.05;

                    n.leftArm.rotation.y = 0;

                }

                if (n.rightArm) {

                    n.rightArm.rotation.x = -2.2;

                    n.rightArm.rotation.z = 0.45 - Math.sin(elapsed * 4) * 0.05;

                    n.rightArm.rotation.y = 0;

                }

                if (n.head) n.head.rotation.x = -0.25;



                if (n.stateTime > 3.8) {

                    n.state = 'working';

                    n.stateTime = 0;

                    if (n.leftArm) { n.leftArm.rotation.z = -0.10; n.leftArm.rotation.x = -0.75; n.leftArm.rotation.y = -0.22; }

                    if (n.rightArm) { n.rightArm.rotation.z = 0.10; n.rightArm.rotation.x = -0.75; n.rightArm.rotation.y = 0.22; }

                    if (n.head) n.head.rotation.x = 0;

                }

            } else if (n.state === 'walking_to_wb') {

                if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                    const nextTarget = n.walkWaypoints[0];

                    const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                    diff.y = 0;

                    const dist = diff.length();

                        const step = 2.2 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                } else {

                    n.state = 'presenting';

                    n.stateTime = 0;

                    n.character.position.y = 0.12;

                    n.character.rotation.y = -Math.PI / 2;

                    if (n.leftLeg) n.leftLeg.rotation.x = 0;

                    if (n.rightLeg) n.rightLeg.rotation.x = 0;

                }

            } else if (n.state === 'presenting') {

                if (n.rightArm) {

                    n.rightArm.rotation.x = -1.4 + Math.sin(elapsed * 5) * 0.15;

                    n.rightArm.rotation.z = -0.25;

                }

                if (n.head) {

                    n.head.rotation.y = -Math.PI / 2 + Math.sin(elapsed * 3) * 0.2;

                }



                if (n.stateTime > 6.0) {

                    n.state = 'returning_from_wb';

                    n.stateTime = 0;

                    n.isSitting = false;

                    n.walkWaypoints = this.generateWalkPath(n.character.position, n.homePos);

                }

            } else if (n.state === 'returning_from_wb') {

                if (n.walkWaypoints && n.walkWaypoints.length > 0) {

                    const nextTarget = n.walkWaypoints[0];

                    const diff = new THREE.Vector3().subVectors(nextTarget, n.character.position);

                    diff.y = 0;

                    const dist = diff.length();

                        const step = 2.2 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            n.character.position.addScaledVector(diff, step);

                            n.character.rotation.y = Math.atan2(diff.x, diff.z);

                            n.character.position.y = 0.12 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (n.leftLeg) n.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                            if (n.rightLeg) n.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            if (n.leftArm) n.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (n.rightArm) n.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            n.character.position.x = nextTarget.x;

                            n.character.position.z = nextTarget.z;

                            n.walkWaypoints.shift();

                        }

                } else {

                    n.character.position.copy(n.homePos);

                    n.character.rotation.y = n.homeRot;

                    n.state = 'working';

                    n.stateTime = 0;

                    n.isSitting = true;

                    if (n.leftLeg) n.leftLeg.rotation.x = -Math.PI / 2.2;

                    if (n.rightLeg) n.rightLeg.rotation.x = -Math.PI / 2.2;

                }

            }

        }



        updateAssistantBehaviors(delta, elapsed) {

            const rovingStates = ['walking_to_wb', 'at_whiteboard', 'walking_to_tea', 'drinking_tea', 'walking_to_peer', 'chatting_with_peer', 'walking_to_ceo', 'reporting_to_ceo', 'returning'];

            // YÊU CẦU 1: 12 GHẾ BÀN HỌP (6 ghế dãy Bắc x = 5.75..13.25, 6 ghế dãy Nam x = 5.75..13.25)

            const meetingSideA = [

                new THREE.Vector3(5.75, 0.10, -10.05),

                new THREE.Vector3(7.25, 0.10, -10.05),

                new THREE.Vector3(8.75, 0.10, -10.05),

                new THREE.Vector3(10.25, 0.10, -10.05),

                new THREE.Vector3(11.75, 0.10, -10.05),

                new THREE.Vector3(13.25, 0.10, -10.05)

            ];

            const meetingSideB = [

                new THREE.Vector3(5.75, 0.10, -6.95),

                new THREE.Vector3(7.25, 0.10, -6.95),

                new THREE.Vector3(8.75, 0.10, -6.95),

                new THREE.Vector3(10.25, 0.10, -6.95),

                new THREE.Vector3(11.75, 0.10, -6.95),

                new THREE.Vector3(13.25, 0.10, -6.95)

            ];



            for (let i = 0; i < this.characters.length; i++) {

                const asst = this.characters[i];

                asst.stateTime += delta;



                // YÊU CẦU 1: ĐỘ MỜ BẢNG TÊN TRỢ LÝ / THƯ KÝ KHI VÀO / RA BÀN HỌP

                if (asst.badgeSprite && asst.badgeSprite.material) {

                    let targetOpacity = 1.0;

                    if (this.isMeetingActive || this.isBirthdayActive || asst.state === 'meeting' || asst.state === 'birthday_party') {

                        if (asst.walkPath && asst.walkPath.length > 0) {

                            const dHome = asst.mesh.position.distanceTo(asst.homePos);

                            const dSeat = asst.targetPos ? asst.mesh.position.distanceTo(asst.targetPos) : 1.0;

                            const total = dHome + dSeat;

                            const prog = total > 0.1 ? Math.min(1.0, Math.max(0.0, dHome / total)) : 1.0;

                            targetOpacity = 1.0 - prog * 0.90; // Từ 1.0 giảm dần xuống 0.10

                        } else {

                            targetOpacity = 0.10; // Đã ngồi tại bàn họp: giữ 10%

                        }

                    } else if (asst.state === 'returning') {

                        const dHome = asst.mesh.position.distanceTo(asst.homePos);

                        const dSeat = asst.targetPos ? asst.mesh.position.distanceTo(asst.targetPos) : 4.0;

                        const total = dHome + dSeat;

                        const prog = total > 0.1 ? Math.min(1.0, Math.max(0.0, dSeat / total)) : 1.0;

                        targetOpacity = 0.10 + prog * 0.90; // Từ 0.10 tăng dần lên 1.0

                    } else {

                        targetOpacity = 1.0;

                    }

                    asst.badgeSprite.material.opacity += (targetOpacity - asst.badgeSprite.material.opacity) * Math.min(1.0, delta * 4.0);

                }



                // YEU CAU 4: DANCE PARTY BEHAVIOR KHI PHAT NHAC YOUTUBE

                if (this.isDancingActive) {

                    if (asst.badgeSprite) asst.badgeSprite.visible = false;

                    if (asst.lightbulb) asst.lightbulb.visible = false;



                    if (asst.walkPath && asst.walkPath.length > 0) {

                        const nextTarget = asst.walkPath[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, asst.mesh.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = asst.speed * 2.5 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            asst.mesh.position.addScaledVector(diff, step);

                            asst.mesh.rotation.y = Math.atan2(diff.x, diff.z);

                            asst.mesh.position.y = 0.10 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                                asst.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            }

                            if (asst.leftArm) asst.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (asst.rightArm) asst.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            asst.walkPath.shift();

                        }

                    } else {

                        if (asst.danceRole === 'pair1_partner') {

                            // CẶP ĐÔI 1: SHIZUKA NẮM TAY CIO BẮC NGUYỄN (YÊU CẦU 1: LẮC LƯ, LÂU LÂU MỚI XOAY)

                            const pair1Center = new THREE.Vector3(-1.8, 0, 3.0);

                            const pairCycle = elapsed % 15.0;

                            let spinAngle = 0;

                            if (pairCycle > 11.5) {

                                const spinProg = (pairCycle - 11.5) / 3.5;

                                const smooth = (1 - Math.cos(spinProg * Math.PI)) / 2;

                                spinAngle = smooth * Math.PI * 2;

                            } else {

                                spinAngle = Math.sin(elapsed * 1.5) * 0.6;

                            }

                            const r = 0.62;



                            const posX = pair1Center.x - Math.cos(spinAngle) * r;

                            const posZ = pair1Center.z - Math.sin(spinAngle) * r;

                            const bounceY = 0.10 + Math.abs(Math.sin(elapsed * 6.5)) * 0.16;



                            asst.mesh.position.set(posX, bounceY, posZ);

                            asst.mesh.rotation.y = spinAngle; // Mặt hướng về CIO Bắc Nguyễn

                            asst.mesh.rotation.z = -Math.sin(elapsed * 6.5) * 0.12;



                            if (asst.leftArm) {

                                asst.leftArm.rotation.x = -1.25;

                                asst.leftArm.rotation.z = -0.25;

                            }

                            if (asst.rightArm) {

                                asst.rightArm.rotation.x = -1.25;

                                asst.rightArm.rotation.z = 0.25;

                            }

                            if (asst.leftLeg) asst.leftLeg.rotation.x = -Math.sin(elapsed * 6.5) * 0.45;

                            if (asst.rightLeg) asst.rightLeg.rotation.x = Math.sin(elapsed * 6.5) * 0.45;



                        } else if (asst.danceRole === 'pair2_a') {

                            // CẶP ĐÔI 2 - NHÂN VẬT A (THẠCH SANH): NẮM TAY CÔ TẤM (LÂU LÂU MỚI XOAY)

                            const pair2Center = new THREE.Vector3(1.8, 0, 3.0);

                            const pairCycle2 = (elapsed + 3.0) % 15.0;

                            let spin2 = 0;

                            if (pairCycle2 > 11.5) {

                                const spinProg = (pairCycle2 - 11.5) / 3.5;

                                const smooth = (1 - Math.cos(spinProg * Math.PI)) / 2;

                                spin2 = -smooth * Math.PI * 2;

                            } else {

                                spin2 = -Math.sin(elapsed * 1.5) * 0.6;

                            }

                            const r2 = 0.62;



                            const posX = pair2Center.x + Math.cos(spin2) * r2;

                            const posZ = pair2Center.z + Math.sin(spin2) * r2;

                            const bounceY = 0.10 + Math.abs(Math.sin(elapsed * 6.5)) * 0.16;



                            asst.mesh.position.set(posX, bounceY, posZ);

                            asst.mesh.rotation.y = spin2 + Math.PI;

                            asst.mesh.rotation.z = Math.sin(elapsed * 6.5) * 0.12;



                            if (asst.leftArm) asst.leftArm.rotation.x = -1.25;

                            if (asst.rightArm) asst.rightArm.rotation.x = -1.25;

                            if (asst.leftLeg) asst.leftLeg.rotation.x = Math.sin(elapsed * 6.5) * 0.45;

                            if (asst.rightLeg) asst.rightLeg.rotation.x = -Math.sin(elapsed * 6.5) * 0.45;



                        } else if (asst.danceRole === 'pair2_b') {

                            // CẶP ĐÔI 2 - NHÂN VẬT B (CÔ TẤM): NẮM TAY THẠCH SANH

                            const pair2Center = new THREE.Vector3(1.8, 0, 3.0);

                            const pairCycle2 = (elapsed + 3.0) % 15.0;

                            let spin2 = 0;

                            if (pairCycle2 > 11.5) {

                                const spinProg = (pairCycle2 - 11.5) / 3.5;

                                const smooth = (1 - Math.cos(spinProg * Math.PI)) / 2;

                                spin2 = -smooth * Math.PI * 2;

                            } else {

                                spin2 = -Math.sin(elapsed * 1.5) * 0.6;

                            }

                            const r2 = 0.62;



                            const posX = pair2Center.x - Math.cos(spin2) * r2;

                            const posZ = pair2Center.z - Math.sin(spin2) * r2;

                            const bounceY = 0.10 + Math.abs(Math.sin(elapsed * 6.5)) * 0.16;



                            asst.mesh.position.set(posX, bounceY, posZ);

                            asst.mesh.rotation.y = spin2;

                            asst.mesh.rotation.z = -Math.sin(elapsed * 6.5) * 0.12;



                            if (asst.leftArm) asst.leftArm.rotation.x = -1.25;

                            if (asst.rightArm) asst.rightArm.rotation.x = -1.25;

                            if (asst.leftLeg) asst.leftLeg.rotation.x = -Math.sin(elapsed * 6.5) * 0.45;

                            if (asst.rightLeg) asst.rightLeg.rotation.x = Math.sin(elapsed * 6.5) * 0.45;



                        } else {

                            // SOLO DANCERS (DORAEMON, GIAN, SUNEO, MAI AN TIEM...):

                            // ĐỨNG NHẢY THEO NHỊP ĐIỆU BÀI HÁT, LÂU LÂU MỚI XOAY 1 VÒNG (YÊU CẦU 1)

                            const spot = asst.soloSpot || new THREE.Vector3(0, 0.10, 2.5);

                            const phase = i * 2.1;

                            const bounceY = 0.10 + Math.abs(Math.sin(elapsed * 6.5 + phase)) * 0.18;



                            asst.mesh.position.set(spot.x, bounceY, spot.z);

                            asst.mesh.rotation.z = Math.sin(elapsed * 6.5 + phase) * 0.14; // Lắc lư theo nhịp



                            // Chu kỳ 14 giây: 11 giây đứng nhún nhảy hướng về trước/TV, 3 giây xoay tròn 1 vòng

                            const cycleTime = (elapsed + phase * 2.5) % 14.0;

                            let rotY = 0;

                            if (cycleTime > 11.0) {

                                const spinProg = (cycleTime - 11.0) / 3.0;

                                const smooth = (1 - Math.cos(spinProg * Math.PI)) / 2;

                                rotY = smooth * Math.PI * 2;

                            } else {

                                rotY = Math.sin(elapsed * 2.0 + phase) * 0.22;

                            }

                            asst.mesh.rotation.y = rotY;



                            if (asst.leftArm) {

                                asst.leftArm.rotation.x = Math.sin(elapsed * 6.5 + phase) * 0.6 - 0.3;

                                asst.leftArm.rotation.z = 0.35 + Math.sin(elapsed * 3.2) * 0.2;

                            }

                            if (asst.rightArm) {

                                asst.rightArm.rotation.x = -Math.sin(elapsed * 6.5 + phase) * 0.6 - 0.3;

                                asst.rightArm.rotation.z = -0.35 - Math.sin(elapsed * 3.2) * 0.2;

                            }

                            if (asst.leftLeg) asst.leftLeg.rotation.x = Math.sin(elapsed * 6.5 + phase) * 0.4;

                            if (asst.rightLeg) asst.rightLeg.rotation.x = -Math.sin(elapsed * 6.5 + phase) * 0.4;

                        }

                    }

                    continue;

                }



                if (this.isBirthdayActive) {

                    if (asst.state !== 'birthday_party') {

                        asst.state = 'birthday_party';

                        asst.stateTime = 0;

                        if (asst.lightbulb) asst.lightbulb.visible = false;

                        const seat = (i % 2 === 0) ? meetingSideA[Math.floor(i / 2) % 6] : meetingSideB[Math.floor(i / 2) % 6];

                        asst.targetPos.copy(seat);

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, seat);

                    }



                    if (asst.walkPath && asst.walkPath.length > 0) {

                        const nextTarget = asst.walkPath[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, asst.mesh.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = asst.speed * 2.5 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            asst.mesh.position.addScaledVector(diff, step);

                            asst.mesh.rotation.y = Math.atan2(diff.x, diff.z);

                            asst.mesh.position.y = 0.10 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                                asst.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            }

                            if (asst.leftArm) asst.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (asst.rightArm) asst.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            asst.mesh.position.x = nextTarget.x;

                            asst.mesh.position.z = nextTarget.z;

                            asst.walkPath.shift();

                        }

                    } else {

                        asst.mesh.position.copy(asst.targetPos);

                        asst.mesh.position.y = 0.10;

                        asst.mesh.rotation.y = (i % 2 === 0) ? 0 : Math.PI;

                        // Clapping forward in front of chest!

                        if (asst.leftArm) asst.leftArm.rotation.x = -1.1 + Math.sin(elapsed * 12 + i) * 0.25;

                        if (asst.rightArm) asst.rightArm.rotation.x = -1.1 + Math.cos(elapsed * 12 + i) * 0.25;

                        if (asst.leftLeg && asst.rightLeg) {

                            asst.leftLeg.rotation.x = 0;

                            asst.rightLeg.rotation.x = 0;

                        }

                    }

                    continue;

                }



                if (this.isMeetingActive) {

                    if (asst.state !== 'meeting') {

                        asst.state = 'meeting';

                        asst.stateTime = 0;

                        if (asst.lightbulb) asst.lightbulb.visible = false;

                        const seat = (i % 2 === 0) ? meetingSideA[Math.floor(i / 2) % 6] : meetingSideB[Math.floor(i / 2) % 6];

                        asst.targetPos.copy(seat);

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, seat);

                    }



                    if (asst.walkPath && asst.walkPath.length > 0) {

                        const nextTarget = asst.walkPath[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, asst.mesh.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = asst.speed * 2.5 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            asst.mesh.position.addScaledVector(diff, step);

                            asst.mesh.rotation.y = Math.atan2(diff.x, diff.z);

                            asst.mesh.position.y = 0.10 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                                asst.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            }

                            if (asst.leftArm) asst.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (asst.rightArm) asst.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            asst.mesh.position.x = nextTarget.x;

                            asst.mesh.position.z = nextTarget.z;

                            asst.walkPath.shift();

                        }

                    } else {

                        // Seated comfortably in conference chair with legs under table!

                        asst.mesh.position.copy(asst.targetPos);

                        asst.mesh.position.y = 0.10;

                        asst.mesh.rotation.y = (i % 2 === 0) ? 0 : Math.PI;

                        if (asst.leftLeg && asst.rightLeg) {

                            asst.leftLeg.rotation.x = -Math.PI / 2.2;

                            asst.rightLeg.rotation.x = -Math.PI / 2.2;

                        }

                        if (asst.leftArm) asst.leftArm.rotation.x = -0.80 + Math.sin(elapsed * 5 + i) * 0.10;

                        if (asst.rightArm) asst.rightArm.rotation.x = -0.80 + Math.cos(elapsed * 5 + i) * 0.10;

                    }

                    continue;

                }



                // HET SINH NHAT HOAC HET HOP -> MOI TRO LY DEU QUAY VE BAN LAM VIEC CUA MINH

                

                // ==================== CÔ TẤM BÁO CÁO LỊCH TRÌNH VỚI CIO BẮC NGUYỄN ====================

                if (asst.state === 'tam_walking_to_cio') {

                    if (asst.walkPath && asst.walkPath.length > 0) {

                        const nextTarget = asst.walkPath[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, asst.mesh.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = asst.speed * 2.6 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            asst.mesh.position.addScaledVector(diff, step);

                            asst.mesh.rotation.y = Math.atan2(diff.x, diff.z);

                            asst.mesh.position.y = 0.10 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                                asst.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            }

                            if (asst.leftArm) asst.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (asst.rightArm) asst.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            asst.mesh.position.x = nextTarget.x;

                            asst.mesh.position.z = nextTarget.z;

                            asst.walkPath.shift();

                        }

                    } else {

                        // Đã đến trước bàn làm việc CIO!

                        asst.state = 'tam_speaking_to_cio';

                        asst.stateTime = 0;

                        asst.mesh.rotation.y = Math.PI; // hướng về phía CIO

                        if (asst.leftLeg && asst.rightLeg) {

                            asst.leftLeg.rotation.x = 0;

                            asst.rightLeg.rotation.x = 0;

                        }

                        if (asst.head) asst.head.rotation.x = 0.35; // cúi đầu chào



                        this.showSpeechBubble(asst, asst.speechText);

                        const speechLen = asst.speechText ? asst.speechText.length : 60;

                        asst.reportDuration = Math.max(6.0, speechLen * 0.08);



                        if (!this.isVoiceMuted && typeof window.speakVietnamese === 'function') {

                            window.speakVietnamese(asst.speechText, () => {

                                asst.stateTime = asst.reportDuration;

                            });

                        }

                    }

                    continue;

                }



                if (asst.state === 'tam_speaking_to_cio') {

                    asst.mesh.rotation.y = Math.PI;

                    if (asst.leftArm) asst.leftArm.rotation.x = -0.6 + Math.sin(elapsed * 3) * 0.12;

                    if (asst.rightArm) asst.rightArm.rotation.x = -0.6 + Math.cos(elapsed * 3) * 0.12;

                    if (asst.head) {

                        if (asst.stateTime < 1.0) {

                            asst.head.rotation.x = 0.35;

                        } else if (asst.stateTime > asst.reportDuration - 1.2) {

                            asst.head.rotation.x = 0.35; // Cúi chào khi kết thúc câu

                        } else {

                            asst.head.rotation.x = 0.05 + Math.sin(elapsed * 4) * 0.05;

                        }

                    }



                    if (asst.stateTime >= asst.reportDuration) {

                        this.hideSpeechBubble(asst);

                        if (asst.head) asst.head.rotation.x = 0;

                        asst.state = 'returning';

                        asst.stateTime = 0;

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

                        if (asst.onReportDone) {

                            try { asst.onReportDone(); } catch(e){}

                            asst.onReportDone = null;

                        }

                    }

                    continue;

                }



                if (asst.state === 'birthday_party' || asst.state === 'meeting') {

                    asst.state = 'returning';

                    asst.stateTime = 0;

                    asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

                }



                // UNIVERSAL SAFETY WATCHDOG FOR ASSISTANTS: If away from desk for > 22s (not in meeting or birthday), reset to desk

                if (asst.state !== 'working' && !this.isBirthdayActive && !this.isMeetingActive && !this.isDancingActive && asst.stateTime > 22.0) {

                    asst.mesh.position.copy(asst.homePos);

                    asst.mesh.rotation.y = asst.homeRot;

                    asst.mesh.position.y = 0.10;

                    asst.state = 'working';

                    asst.stateTime = 0;

                    if (asst.leftLeg && asst.rightLeg) {

                        asst.leftLeg.rotation.x = -Math.PI / 2.2;

                        asst.rightLeg.rotation.x = -Math.PI / 2.2;

                    }

                    asst.walkPath = [];

                }



                // 1. NGỒI LÀM VIỆC TẠI BÀN (STATE: working)

                if (asst.state === 'working') {

                    if (asst.lightbulb) asst.lightbulb.visible = false;

                    if (asst.leftLeg && asst.rightLeg) {

                        asst.leftLeg.rotation.x = -Math.PI / 2.2;

                        asst.rightLeg.rotation.x = -Math.PI / 2.2;

                    }

                    if (asst.leftArm) asst.leftArm.rotation.x = -0.80 + Math.sin(elapsed * 6 + asst.homePos.x) * 0.05;

                    if (asst.rightArm) asst.rightArm.rotation.x = -0.80 + Math.cos(elapsed * 5 + asst.homePos.z) * 0.05;



                    // Chu kỳ hoạt động định kỳ: thỉnh thoảng đứng dậy đi lại (25s - 45s)

                    const routineInterval = 25 + (i * 12);

                    if (asst.stateTime > routineInterval && !asst.isAiActive) {

                        // Kiểm tra xem hiện có trợ lý nào khác đang rời bàn không (mỗi thời điểm chỉ 1 người rời bàn để giữ trật tự văn phòng)

                        const isAnyoneAway = this.characters.some(c => c.id !== asst.id && rovingStates.includes(c.state));

                        if (!isAnyoneAway) {

                            const randChoice = Math.random();

                            if (randChoice < 0.25) {

                                // Hoạt động 1: Lên bảng Chiến lược xem chỉ trỏ

                                asst.state = 'walking_to_wb';

                                asst.stateTime = 0;

                                const wbTarget = new THREE.Vector3(-14.2, 0.10, 7.5);

                                asst.walkPath = this.generateWalkPath(asst.mesh.position, wbTarget);

                            } else if (randChoice < 0.50) {

                                // Hoạt động 2: Lại bàn ngồi uống trà

                                asst.state = 'walking_to_tea';

                                asst.stateTime = 0;

                                const teaTarget = new THREE.Vector3(10.5, 0.10, 8.0);

                                asst.walkPath = this.generateWalkPath(asst.mesh.position, teaTarget);

                            } else if (randChoice < 0.75) {

                                // Hoạt động 3: Lại bàn trợ lý khác nói chuyện

                                const peers = this.characters.filter(c => c.id !== asst.id && c.state === 'working');

                                if (peers.length > 0) {

                                    const peer = peers[Math.floor(Math.random() * peers.length)];

                                    asst.peerTargetId = peer.id;

                                    asst.state = 'walking_to_peer';

                                    asst.stateTime = 0;

                                    const sideOffset = peer.homePos.x >= 0 ? -1.1 : 1.1;

                                    const peerDest = new THREE.Vector3(peer.homePos.x + sideOffset, 0.10, peer.homePos.z + 0.5);

                                    asst.walkPath = this.generateWalkPath(asst.mesh.position, peerDest);

                                } else {

                                    asst.state = 'walking_to_ceo';

                                    asst.stateTime = 0;

                                    const ceoFrontPos = new THREE.Vector3(-0.6 + (i % 2) * 1.2, 0.10, -0.60);

                                    asst.walkPath = this.generateWalkPath(asst.mesh.position, ceoFrontPos);

                                }

                            } else {

                                // Hoạt động 4: Lại bàn CEO báo cáo trong vòng 5s

                                asst.state = 'walking_to_ceo';

                                asst.stateTime = 0;

                                const ceoFrontPos = new THREE.Vector3(-0.6 + (i % 2) * 1.2, 0.10, -0.60);

                                asst.walkPath = this.generateWalkPath(asst.mesh.position, ceoFrontPos);

                            }

                        }

                    }

                } 

                // 2. TẬP TRUNG XỬ LÝ DỮ LIỆU / SUY NGHĨ (STATE: busy_working)

                else if (asst.state === 'busy_working') {

                    if (asst.leftLeg && asst.rightLeg) {

                        asst.leftLeg.rotation.x = -Math.PI / 2.2;

                        asst.rightLeg.rotation.x = -Math.PI / 2.2;

                    }

                    if (asst.lightbulb) {

                        asst.lightbulb.visible = true;

                        asst.lightbulb.scale.setScalar(1.0 + Math.sin(elapsed * 6) * 0.15);

                    }

                    if (asst.leftArm) asst.leftArm.rotation.x = -0.88 + Math.sin(elapsed * 18) * 0.10;

                    if (asst.rightArm) asst.rightArm.rotation.x = -0.88 + Math.cos(elapsed * 17) * 0.10;



                    if (Math.random() < 0.25) {

                        this.audioPlayer.playKeyboardClick();

                    }



                    // Nếu không phải đang xử lý AI query từ người dùng, tự động kết thúc sau 6s

                    if (!asst.isAiActive && asst.stateTime > 6.0) {

                        asst.state = 'working';

                        asst.stateTime = 0;

                        if (asst.lightbulb) asst.lightbulb.visible = false;

                    }

                }

                // 3. DI CHUYỂN TRONG CÁC HOẠT ĐỘNG (walking_to_wb, walking_to_tea, walking_to_peer, walking_to_ceo, returning)

                else if (['walking_to_wb', 'walking_to_tea', 'walking_to_peer', 'walking_to_ceo', 'returning'].includes(asst.state)) {

                    if (asst.walkPath && asst.walkPath.length > 0) {

                        const nextTarget = asst.walkPath[0];

                        const diff = new THREE.Vector3().subVectors(nextTarget, asst.mesh.position);

                        diff.y = 0;

                        const dist = diff.length();

                        const step = asst.speed * 2.5 * delta;

                        if (dist > 0.32 && dist > step) {

                            diff.normalize();

                            asst.mesh.position.addScaledVector(diff, step);

                            asst.mesh.rotation.y = Math.atan2(diff.x, diff.z);

                            asst.mesh.position.y = 0.10 + Math.abs(Math.sin(elapsed * 9)) * 0.12;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = Math.sin(elapsed * 9) * 0.45;

                                asst.rightLeg.rotation.x = -Math.sin(elapsed * 9) * 0.45;

                            }

                            if (asst.leftArm) asst.leftArm.rotation.x = Math.sin(elapsed * 9) * 0.35;

                            if (asst.rightArm) asst.rightArm.rotation.x = -Math.sin(elapsed * 9) * 0.35;

                        } else {

                            asst.mesh.position.x = nextTarget.x;

                            asst.mesh.position.z = nextTarget.z;

                            asst.walkPath.shift();

                        }

                    } else {

                        // ĐÃ ĐẾN NƠI -> CHUYỂN SANG TRẠNG THÁI TƯƠNG ỨNG

                        if (asst.state === 'walking_to_wb') {

                            asst.state = 'at_whiteboard';

                            asst.stateTime = 0;

                            asst.mesh.position.set(-14.2, 0.10, 7.5);

                            asst.mesh.rotation.y = -Math.PI / 2; // Nhìn vào bảng chiến lược

                            if (asst.leftLeg && asst.rightLeg) { asst.leftLeg.rotation.x = 0; asst.rightLeg.rotation.x = 0; }

                        } else if (asst.state === 'walking_to_tea') {

                            asst.state = 'drinking_tea';

                            asst.stateTime = 0;

                            asst.mesh.position.set(10.5, 0.10, 8.0);

                            asst.mesh.rotation.y = Math.PI; // Ngồi trên sofa hướng về bàn trà

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = -Math.PI / 2.2; // Tư thế ngồi sofa

                                asst.rightLeg.rotation.x = -Math.PI / 2.2;

                            }

                        } else if (asst.state === 'walking_to_peer') {

                            asst.state = 'chatting_with_peer';

                            asst.stateTime = 0;

                            const peer = this.characters.find(c => c.id === asst.peerTargetId);

                            if (peer) {

                                asst.mesh.rotation.y = Math.atan2(peer.homePos.x - asst.mesh.position.x, peer.homePos.z - asst.mesh.position.z);

                            }

                            if (asst.leftLeg && asst.rightLeg) { asst.leftLeg.rotation.x = 0; asst.rightLeg.rotation.x = 0; }

                        } else if (asst.state === 'walking_to_ceo') {

                            asst.state = 'reporting_to_ceo';

                            asst.stateTime = 0;

                            asst.mesh.position.set(0, 0.10, -0.60);

                            asst.mesh.rotation.y = Math.PI; // Đứng đối diện CEO Bắc Nguyễn

                            if (asst.leftLeg && asst.rightLeg) { asst.leftLeg.rotation.x = 0; asst.rightLeg.rotation.x = 0; }

                        } else if (asst.state === 'returning') {

                            asst.mesh.position.copy(asst.homePos);

                            asst.mesh.rotation.y = asst.homeRot;

                            asst.mesh.position.y = 0.10;

                            asst.state = 'working';

                            asst.stateTime = 0;

                            if (asst.leftLeg && asst.rightLeg) {

                                asst.leftLeg.rotation.x = -Math.PI / 2.2;

                                asst.rightLeg.rotation.x = -Math.PI / 2.2;

                            }

                        }

                    }

                }

                // 4. LÊN BẢNG CHIẾN LƯỢC XEM VÀ CHỈ TRỎ (STATE: at_whiteboard)

                else if (asst.state === 'at_whiteboard') {

                    // Tay phải chỉ vào sơ đồ trên bảng chiến lược

                    if (asst.rightArm) {

                        asst.rightArm.rotation.x = -1.45 + Math.sin(elapsed * 4) * 0.18;

                        asst.rightArm.rotation.z = -0.25;

                    }

                    if (asst.leftArm) asst.leftArm.rotation.x = 0;

                    if (asst.head) {

                        asst.head.rotation.y = -Math.PI / 2 + Math.sin(elapsed * 2) * 0.15;

                        asst.head.rotation.x = -0.15; // Ngước nhìn bảng

                    }



                    // Xem và chỉ trỏ trong 5 giây rồi quay về bàn làm việc

                    if (asst.stateTime > 5.0) {

                        if (asst.rightArm) asst.rightArm.rotation.z = 0;

                        if (asst.head) { asst.head.rotation.x = 0; asst.head.rotation.y = 0; }

                        asst.state = 'returning';

                        asst.stateTime = 0;

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

                    }

                }

                // 5. LẠI BÀN NGỒI UỐNG TRÀ THƯ GIÃN (STATE: drinking_tea)

                else if (asst.state === 'drinking_tea') {

                    // Nâng tách trà lên uống

                    if (asst.rightArm) asst.rightArm.rotation.x = -1.25 + Math.sin(elapsed * 2.5) * 0.12;

                    if (asst.leftArm) asst.leftArm.rotation.x = -1.05;

                    if (asst.head) asst.head.rotation.y = Math.PI + Math.sin(elapsed * 1.5) * 0.10;



                    // Ngồi uống trà trong 6 giây rồi quay về bàn làm việc

                    if (asst.stateTime > 6.0) {

                        if (asst.head) asst.head.rotation.y = 0;

                        asst.state = 'returning';

                        asst.stateTime = 0;

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

                    }

                }

                // 6. LẠI BÀN ĐỒNG NGHIỆP TRÒ CHUYỆN (STATE: chatting_with_peer)

                else if (asst.state === 'chatting_with_peer') {

                    // Cử chỉ nói chuyện, trao đổi với đồng nghiệp

                    if (asst.leftArm) asst.leftArm.rotation.x = -0.70 + Math.sin(elapsed * 5) * 0.20;

                    if (asst.rightArm) asst.rightArm.rotation.x = -0.85 + Math.cos(elapsed * 4) * 0.18;

                    if (asst.head) asst.head.rotation.y = Math.sin(elapsed * 3) * 0.15;



                    // Nói chuyện trong 5 giây rồi quay về bàn làm việc

                    if (asst.stateTime > 5.0) {

                        if (asst.head) asst.head.rotation.y = 0;

                        asst.state = 'returning';

                        asst.stateTime = 0;

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

                    }

                }

                // 7. LẠI BÀN CEO BÁO CÁO CÔNG VIỆC TRONG VÒNG 5S (STATE: reporting_to_ceo)

                else if (asst.state === 'reporting_to_ceo') {

                    // Cử chỉ báo cáo công việc cho CEO Bắc Nguyễn

                    if (asst.rightArm) asst.rightArm.rotation.x = -1.15 + Math.sin(elapsed * 4) * 0.12;

                    if (asst.head) asst.head.rotation.x = Math.sin(elapsed * 3) * 0.12;



                    // CEO Bắc Nguyễn lắng nghe và gật đầu đáp lại

                    if (this.nobita && this.nobita.head && this.nobita.state === 'working') {

                        this.nobita.head.rotation.x = Math.sin(elapsed * 3) * 0.12;

                    }



                    // Báo cáo trong vòng đúng 5 giây theo yêu cầu của người dùng

                    if (asst.stateTime > 5.0) {

                        asst.state = 'returning';

                        asst.stateTime = 0;

                        asst.walkPath = this.generateWalkPath(asst.mesh.position, asst.homePos);

                    }

                }

            }

        }



        

        // =========================================================================

        // THƯ KÝ CÔ TẤM ĐI ĐẾN TRƯỚC BÀN CIO BÁO CÁO (YÊU CẦU MỚI: TỔNG THƯ KÝ)

        // =========================================================================

        reportToCIOByCoTam(speechText, onDone) {

            let coTam = this.characters.find(c => c.isChiefSecretary || c.id === 'chief_co_tam') ||

                        this.characters.find(c => 

                            (c.characterName && (c.characterName.toLowerCase().includes('tấm') || c.characterName.toLowerCase().includes('tam'))) ||

                            (c.name && (c.name.toLowerCase().includes('tấm') || c.name.toLowerCase().includes('tam')))

                        );

            if (!coTam && this.characters.length > 0) {

                coTam = this.characters[0];

            }

            if (!coTam) return;



            this.isMeetingActive = false;

            coTam.isSitting = false;

            coTam.state = 'tam_walking_to_cio';

            coTam.stateTime = 0;

            coTam.speechText = speechText || "Dạ, em xin báo cáo Sếp Bắc. Em báo cáo hết ạ.";

            coTam.onReportDone = onDone;



            // Đứng tại vị trí trang trọng trước bàn CIO Bắc Nguyễn (x = 0, z = -0.90)

            const cioFront = new THREE.Vector3(0.0, 0.10, -0.90);

            coTam.walkPath = this.generateWalkPath(coTam.mesh.position, cioFront);



            // Xoay góc nhìn camera nhẹ nhàng hướng về bàn làm việc của CIO

            if (this.cameraTarget) {

                this.cameraTarget.set(0.0, 1.4, -2.0);

                this.cameraRadius = 20;

                this.cameraAngleH = Math.PI / 4 + 0.10;

                this.cameraAngleV = Math.PI / 6.0;

                this.updateCameraPosition();

            }

        }



        showSpeechBubble(charObj, text) {

            // Theo yêu cầu của Sếp Bắc: Không hiển thị hình chữ nhật nền trắng phía sau Thư ký Cô Tấm báo cáo CIO

            this.hideSpeechBubble(charObj);

            return;

        }



        hideSpeechBubble(charObj) {

            if (charObj && charObj.speechBubbleSprite) {

                charObj.mesh.remove(charObj.speechBubbleSprite);

                if (charObj.speechBubbleSprite.material) {

                    if (charObj.speechBubbleSprite.material.map) charObj.speechBubbleSprite.material.map.dispose();

                    charObj.speechBubbleSprite.material.dispose();

                }

                charObj.speechBubbleSprite = null;

            }

        }



        toggleVoiceMute() {

            this.isVoiceMuted = !this.isVoiceMuted;

            this.updateVoiceMuteButton();

            return this.isVoiceMuted;

        }



        setVoiceMute(muted) {

            this.isVoiceMuted = !!muted;

            this.updateVoiceMuteButton();

        }



        updateVoiceMuteButton() {

            const btn = document.getElementById('officeVoiceMuteBtn');

            if (btn) {

                if (this.isVoiceMuted) {

                    btn.className = 'px-2.5 py-1.5 text-xs font-bold rounded-lg border-2 transition flex items-center space-x-1.5 shadow-xs cursor-pointer bg-slate-100 text-slate-500 border-slate-300 hover:bg-slate-200';

                    btn.innerHTML = '<i class="fa-solid fa-volume-xmark text-slate-400 text-[11px]"></i><span>Loa nhắc: TẮT</span>';

                } else {

                    btn.className = 'px-2.5 py-1.5 text-xs font-bold rounded-lg border-2 transition flex items-center space-x-1.5 shadow-xs cursor-pointer bg-emerald-50 text-emerald-800 border-emerald-400 hover:bg-emerald-100';

                    btn.innerHTML = '<i class="fa-solid fa-volume-high text-emerald-600 text-[11px]"></i><span>Loa nhắc: BẬT</span>';

                }

            }

        }



        startMeeting() {

            this.isMeetingActive = true;

            this.meetingTimer = 0;

            setTimeout(() => {

                this.isMeetingActive = false;

                this.meetingTimer = 0;

            }, 20000);

        }



        triggerAssistantWork(asstId) {

            let asst = this.characters.find(c => c.id === asstId);

            if (!asst && this.characters.length > 0) asst = this.characters[0];

            if (asst) {

                asst.isAiActive = true;

                asst.state = 'busy_working';

                asst.stateTime = 0;

                asst.mesh.position.copy(asst.homePos);

                asst.mesh.rotation.y = asst.homeRot;

                if (asst.lightbulb) {

                    asst.lightbulb.visible = true;

                    asst.lightbulb.scale.setScalar(1.2);

                }

            }

        }



        finishAssistantWork(asstId) {

            let asst = this.characters.find(c => c.id === asstId);

            if (!asst) asst = this.characters.find(c => c.isAiActive) || this.characters[0];

            if (asst) {

                asst.isAiActive = false;

                if (asst.lightbulb) asst.lightbulb.visible = false;

                // Khi AI trả lời xong: Lập tức đứng dậy, đi đến trước bàn CEO Bắc Nguyễn để báo cáo công việc!

                asst.state = 'walking_to_ceo';

                asst.stateTime = 0;

                const ceoFrontPos = new THREE.Vector3(0, 0.10, -0.60);

                asst.walkPath = this.generateWalkPath(asst.mesh.position, ceoFrontPos);

            }

        }



        // =========================================================================

        // 14. RAYCAST & INTERACTION LISTENERS (CLICK NHÂN VẬT & BẢNG TÊN)

        // =========================================================================

        performRaycastClick(clientX, clientY) {

            if (!this.container || !this.camera || !this.clickableObjects || this.clickableObjects.length === 0) return;

            const rect = this.container.getBoundingClientRect();

            if (rect.width <= 0 || rect.height <= 0) return;



            this.mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1;

            this.mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;



            this.raycaster.setFromCamera(this.mouse, this.camera);

            const intersects = this.raycaster.intersectObjects(this.clickableObjects, true);



            if (intersects.length > 0) {

                let targetData = null;

                // ƯU TIÊN 1: Nếu người dùng click trúng BẢNG TÊN HÌNH CHỮ NHẬT (isSprite), lấy ngay userData của nhân vật đó!

                const spriteHit = intersects.find(h => h.object && h.object.isSprite && h.object.userData && h.object.userData.isAssistant);

                if (spriteHit) {

                    targetData = spriteHit.object.userData;

                } else {

                    for (const hit of intersects) {

                        let cur = hit.object;

                        while (cur) {

                            if (cur.userData && cur.userData.isAssistant) {

                                targetData = cur.userData;

                                break;

                            }

                            cur = cur.parent;

                        }

                        if (targetData) break;

                    }

                }



                if (targetData) {

                    this.showCharacterPopup(targetData);

                } else {

                    const existing = document.getElementById('office3dCharPopup');

                    if (existing) existing.remove();

                }

            } else {

                const existing = document.getElementById('office3dCharPopup');

                if (existing) existing.remove();

            }

        }



        createVideoOverlay() {

            if (!this.container) return;

            let overlay = document.getElementById('officeVideoOverlay');

            if (!overlay) {

                overlay = document.createElement('div');

                overlay.id = 'officeVideoOverlay';

                overlay.className = 'absolute pointer-events-auto rounded shadow-2xl overflow-hidden border-2 border-slate-700 bg-black';

                overlay.style.display = 'none';

                overlay.style.position = 'absolute';

                overlay.style.zIndex = '25';

                overlay.innerHTML = `

                    <div class="relative w-full h-full">

                        <iframe id="officeVideoIframe" class="w-full h-full border-0" src="" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

                        <button type="button" onclick="window.DoraemonOfficeController && window.DoraemonOfficeController.stopVideo()" class="absolute top-1 right-1 bg-black/80 hover:bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px] shadow transition z-30 cursor-pointer" title="Dong TV">X</button>

                    </div>

                `;

                this.container.appendChild(overlay);

            }

            this.videoOverlayEl = overlay;

        }



        updateVideoOverlayPosition() {

            if (!this.isVideoPlaying || !this.tvScreenMesh) {

                if (this.videoOverlayEl) this.videoOverlayEl.style.display = 'none';

                if (this.tvGroup) this.tvGroup.visible = false;

                return;

            }



            if (!this.container) return;

            const containerW = this.container.clientWidth;

            const containerH = this.container.clientHeight;

            if (containerW <= 0 || containerH <= 0) return;



            if (!this.videoOverlayEl) {

                this.createVideoOverlay();

            }



            // MÀN HÌNH CHIẾU YOUTUBE GẤP 3 KÍCH THƯỚC (YÊU CẦU 3): 12.6m x 7.1m

            const halfW = 6.3;

            const halfH = 3.55;

            const localCorners = [

                new THREE.Vector3(-halfW, halfH, 0.05),

                new THREE.Vector3(halfW, halfH, 0.05),

                new THREE.Vector3(halfW, -halfH, 0.05),

                new THREE.Vector3(-halfW, -halfH, 0.05)

            ];



            const screenPoints = [];

            let isBehind = false;



            for (let lc of localCorners) {

                const wp = lc.clone();

                this.tvScreenMesh.localToWorld(wp);



                // Check camera near plane guard

                const camSpace = wp.clone().applyMatrix4(this.camera.matrixWorldInverse);

                if (camSpace.z >= -0.1) {

                    isBehind = true;

                    break;

                }



                const sp = wp.clone().project(this.camera);

                if (sp.z > 1.0) {

                    isBehind = true;

                    break;

                }

                screenPoints.push({

                    x: (sp.x * 0.5 + 0.5) * containerW,

                    y: (-sp.y * 0.5 + 0.5) * containerH

                });

            }



            if (isBehind || screenPoints.length < 4) {

                this.videoOverlayEl.style.display = 'none';

                return;

            }



            const minX = Math.min(screenPoints[0].x, screenPoints[1].x, screenPoints[2].x, screenPoints[3].x);

            const maxX = Math.max(screenPoints[0].x, screenPoints[1].x, screenPoints[2].x, screenPoints[3].x);

            const minY = Math.min(screenPoints[0].y, screenPoints[1].y, screenPoints[2].y, screenPoints[3].y);

            const maxY = Math.max(screenPoints[0].y, screenPoints[1].y, screenPoints[2].y, screenPoints[3].y);



            const w = maxX - minX;

            const h = maxY - minY;



            if (w < 40 || h < 25) {

                this.videoOverlayEl.style.display = 'none';

                return;

            }



            this.videoOverlayEl.style.display = 'block';

            this.videoOverlayEl.style.left = `${Math.round(minX)}px`;

            this.videoOverlayEl.style.top = `${Math.round(minY)}px`;

            this.videoOverlayEl.style.width = `${Math.round(w)}px`;

            this.videoOverlayEl.style.height = `${Math.round(h)}px`;

        }



        playVideo(videoInput) {

            const videoId = extractYouTubeId(videoInput || this.currentVideoId || 'https://www.youtube.com/watch?v=3S6R-nOA2eY');

            this.currentVideoId = videoId;

            this.currentVideoUrl = `https://www.youtube.com/watch?v=${videoId}`;

            this.isVideoPlaying = true;



            // Auto pause BGM

            if (this.audioPlayer && this.audioPlayer.isPlaying) {

                this.wasBgmPlayingBeforeVideo = true;

                this.audioPlayer.pause();

            } else {

                this.wasBgmPlayingBeforeVideo = false;

            }



            if (!this.videoOverlayEl) {

                this.createVideoOverlay();

            }



            const iframe = document.getElementById('officeVideoIframe');

            if (iframe) {

                iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&enablejsapi=1&rel=0`;

            }

            if (this.videoOverlayEl) {

                this.videoOverlayEl.style.display = 'block';

            }



            // Update UI buttons

            const playLabel = document.getElementById('officePlayVideoLabel');

            const playIcon = document.getElementById('officePlayVideoIcon');

            const stopBtn = document.getElementById('officeStopVideoBtn');

            if (playLabel) playLabel.textContent = 'đang phát';

            if (playIcon) playIcon.className = 'fa-solid fa-circle-play text-[10px] animate-pulse';

            if (stopBtn) stopBtn.classList.remove('hidden');



            if (this.tvGroup) {

                this.tvGroup.visible = true;

            }



            this.updateVideoOverlayPosition();



            // YEU CAU 4: BAT DAU DANCE PARTY GIUA PHONG VA AN BẢNG TEN TRÊN ĐẦU

            this.startDanceParty();

        }



        stopVideo() {

            this.isVideoPlaying = false;

            const iframe = document.getElementById('officeVideoIframe');

            if (iframe) {

                iframe.src = '';

            }

            if (this.videoOverlayEl) {

                this.videoOverlayEl.style.display = 'none';

            }

            if (this.tvGroup) {

                this.tvGroup.visible = false;

            }



            // Resume BGM if it was playing before

            if (this.wasBgmPlayingBeforeVideo && this.audioPlayer) {

                this.audioPlayer.play();

            }



            // Update UI buttons

            const playLabel = document.getElementById('officePlayVideoLabel');

            const playIcon = document.getElementById('officePlayVideoIcon');

            const stopBtn = document.getElementById('officeStopVideoBtn');

            if (playLabel) playLabel.textContent = 'Phát';

            if (playIcon) playIcon.className = 'fa-solid fa-play text-[10px]';

            if (stopBtn) stopBtn.classList.add('hidden');



            // YEU CAU 4: KET THUC DANCE PARTY, HIEN LAI BẢNG TEN VA DI CHUYEN VE CHO

            this.endDanceParty();

        }



        startDanceParty() {

            this.isDancingActive = true;

            this.danceTimer = 0;



            // 1. AN KHUNG CHU NHAT / BẢNG TEN TREN DAU TAT CA NHAN VAT

            if (this.nobita && this.nobita.badgeSprite) {

                this.nobita.badgeSprite.visible = false;

            }

            if (this.characters && this.characters.length > 0) {

                for (const char of this.characters) {

                    if (char.badgeSprite) char.badgeSprite.visible = false;

                    if (char.lightbulb) char.lightbulb.visible = false;

                }

            }



            // 2. CIO BAC NGUYEN DI RA KHU VUC GIUA PHONG (KHONG GAN BAN, z >= 2.5)

            if (this.nobita) {

                this.nobita.isSitting = false;

                this.nobita.state = 'dancing';

                this.nobita.stateTime = 0;

                const danceCenter1 = new THREE.Vector3(-1.8, 0.12, 3.0);

                this.nobita.walkWaypoints = this.generateWalkPath(this.nobita.character.position, danceCenter1);

            }



            // 3. CAC TRO LY VA THU KY TAP TRUNG RA GIUA PHONG

            if (this.characters && this.characters.length > 0) {

                this.assignDanceRoles();

                for (const char of this.characters) {

                    char.state = 'dancing';

                    char.stateTime = 0;

                    if (char.targetPos) {

                        char.walkPath = this.generateWalkPath(char.mesh.position, char.targetPos);

                    }

                }

            }

        }



        assignDanceRoles() {

            if (!this.characters || this.characters.length === 0) return;



            let pair1Partner = this.characters.find(c => 

                (c.characterName && c.characterName.toLowerCase().includes('shizuka')) ||

                (c.name && c.name.toLowerCase().includes('shizuka'))

            );

            if (!pair1Partner && this.characters.length > 0) {

                pair1Partner = this.characters[0];

            }



            let pair2A = this.characters.find(c => 

                c !== pair1Partner && (

                    (c.characterName && (c.characterName.toLowerCase().includes('sanh') || c.characterName.toLowerCase().includes('thạch'))) ||

                    (c.name && (c.name.toLowerCase().includes('sanh') || c.name.toLowerCase().includes('thạch')))

                )

            );

            let pair2B = this.characters.find(c => 

                c !== pair1Partner && c !== pair2A && (

                    (c.characterName && (c.characterName.toLowerCase().includes('tấm') || c.characterName.toLowerCase().includes('tam'))) ||

                    (c.name && (c.name.toLowerCase().includes('tấm') || c.name.toLowerCase().includes('tam')))

                )

            );



            const remaining = this.characters.filter(c => c !== pair1Partner);

            if (!pair2A && remaining.length > 0) pair2A = remaining[0];

            if (!pair2B && remaining.length > 1) pair2B = remaining[1];



            for (const c of this.characters) {

                c.danceRole = 'solo';

            }



            if (pair1Partner) {

                pair1Partner.danceRole = 'pair1_partner';

                pair1Partner.targetPos = new THREE.Vector3(-1.2, 0.10, 3.0);

            }



            if (pair2A && pair2B) {

                pair2A.danceRole = 'pair2_a';

                pair2A.targetPos = new THREE.Vector3(1.2, 0.10, 3.0);

                pair2B.danceRole = 'pair2_b';

                pair2B.targetPos = new THREE.Vector3(2.4, 0.10, 3.0);

            }



            const soloDancers = this.characters.filter(c => c.danceRole === 'solo');

            // Toan bo vi tri nhay deu nam o khoang san rong giua phong (z: 1.5 den 4.8), hoan toan cach xa ban lam viec (z <= -1.6)

            const soloSpots = [

                new THREE.Vector3(0.0, 0.10, 1.6),   // Doraemon (truoc ban, cach xa ban)

                new THREE.Vector3(-3.8, 0.10, 2.5),  // Gian

                new THREE.Vector3(3.8, 0.10, 2.5),   // Suneo

                new THREE.Vector3(0.0, 0.10, 4.6),   // Mai An Tiem

                new THREE.Vector3(-2.6, 0.10, 4.5),

                new THREE.Vector3(2.6, 0.10, 4.5),

                new THREE.Vector3(-4.0, 0.10, 4.2),

                new THREE.Vector3(4.0, 0.10, 4.2)

            ];



            soloDancers.forEach((c, idx) => {

                c.soloSpot = soloSpots[idx % soloSpots.length].clone();

                c.targetPos = c.soloSpot.clone();

            });

        }



        endDanceParty() {

            this.isDancingActive = false;

            this.danceTimer = 0;



            // 1. HIEN LAI BẢNG TEN TREN DAU NHAN VAT

            if (this.nobita && this.nobita.badgeSprite) {

                this.nobita.badgeSprite.visible = true;

                if (this.nobita.badgeSprite.material) {

                    this.nobita.badgeSprite.material.opacity = 1.0;

                }

            }

            if (this.characters && this.characters.length > 0) {

                for (const char of this.characters) {

                    if (char.badgeSprite) {

                        char.badgeSprite.visible = true;

                        if (char.badgeSprite.material) {

                            char.badgeSprite.material.opacity = 1.0;

                        }

                    }

                }

            }



            // 2. RESET GOC NGHIENG VA CHO CIO VE BAN

            if (this.nobita) {

                this.nobita.character.rotation.z = 0;

                this.nobita.state = 'returning_from_party';

                this.nobita.stateTime = 0;

                this.nobita.walkWaypoints = this.generateWalkPath(this.nobita.character.position, this.nobita.homePos);

            }



            // 3. CAC TRO LY VA THU KY VE BAN

            if (this.characters && this.characters.length > 0) {

                for (const char of this.characters) {

                    char.mesh.rotation.z = 0;

                    char.state = 'returning';

                    char.stateTime = 0;

                    char.walkPath = this.generateWalkPath(char.mesh.position, char.homePos);

                }

            }

        }



        setupEventListeners() {

            if (!this.container || this._listenersAttached) return;

            this._listenersAttached = true;



            // Listen to YouTube playback events (auto stop when song finishes)

            window.addEventListener('message', (event) => {

                try {

                    let data = event.data;

                    if (typeof data === 'string') {

                        data = JSON.parse(data);

                    }

                    if (data && data.event === 'onStateChange' && data.info === 0) {

                        if (window.DoraemonOfficeController) {

                            window.DoraemonOfficeController.stopVideo();

                        }

                    }

                } catch (e) {}

            });



            document.addEventListener('visibilitychange', () => {

                if (this.clock) {

                    this.clock.getDelta();

                }

            });



            this.dragDistance = 0;

            this.startMousePos = { x: 0, y: 0 };

            this.pointerDownTime = 0;



            // 1. POINTER DOWN (Chuột / Cảm ứng)

            this.container.addEventListener('pointerdown', (e) => {

                if (e.target && e.target.closest && e.target.closest('#office3dCharPopup')) {

                    return;

                }

                this.isDragging = true;

                this.dragDistance = 0;

                this.prevMousePos = { x: e.clientX, y: e.clientY };

                this.startMousePos = { x: e.clientX, y: e.clientY };

                this.pointerDownTime = performance.now();

                try {

                    this.container.setPointerCapture(e.pointerId);

                } catch (err) {}

                this.container.style.cursor = 'grabbing';

            });



            // 2. POINTER MOVE: Xoay góc nhìn phòng 3D mượt mà + Hover effect

            this.container.addEventListener('pointermove', (e) => {

                if (this.isDragging) {

                    const dx = e.clientX - this.prevMousePos.x;

                    const dy = e.clientY - this.prevMousePos.y;

                    this.dragDistance += Math.hypot(dx, dy);



                    this.cameraAngleH -= dx * 0.0055;

                    this.cameraAngleV += dy * 0.0045;

                    this.cameraAngleV = Math.max(0.08, Math.min(Math.PI / 2.15, this.cameraAngleV));

                    this.prevMousePos = { x: e.clientX, y: e.clientY };

                    this.updateCameraPosition();

                } else if (this.container && this.camera && this.clickableObjects.length > 0) {

                    const rect = this.container.getBoundingClientRect();

                    if (rect.width > 0 && rect.height > 0) {

                        const hx = ((e.clientX - rect.left) / rect.width) * 2 - 1;

                        const hy = -((e.clientY - rect.top) / rect.height) * 2 + 1;

                        this.raycaster.setFromCamera({ x: hx, y: hy }, this.camera);

                        const hits = this.raycaster.intersectObjects(this.clickableObjects, true);

                        let isHoverChar = false;

                        if (hits.length > 0) {

                            for (const hit of hits) {

                                let cur = hit.object;

                                while (cur) {

                                    if (cur.userData && cur.userData.isAssistant) {

                                        isHoverChar = true;

                                        break;

                                    }

                                    cur = cur.parent;

                                }

                                if (isHoverChar) break;

                            }

                        }

                        this.container.style.cursor = isHoverChar ? 'pointer' : 'grab';

                    }

                }

            });



            // 3. POINTER UP: Nhả chuột + Nhận diện Click nhạy bén để mở popup tương tác

            this.container.addEventListener('pointerup', (e) => {

                if (this.isDragging) {

                    this.isDragging = false;

                    try {

                        this.container.releasePointerCapture(e.pointerId);

                    } catch (err) {}

                    this.container.style.cursor = 'grab';



                    if (e.target && e.target.closest && e.target.closest('#office3dCharPopup')) {

                        return;

                    }



                    const totalDisp = Math.hypot(e.clientX - this.startMousePos.x, e.clientY - this.startMousePos.y);

                    const elapsed = performance.now() - (this.pointerDownTime || 0);



                    // YÊU CẦU 3: Dung sai nhấp chuột rộng rãi (dưới 20px hoặc dưới 300ms) để nhận diện click hoàn hảo

                    if (this.dragDistance < 20 || totalDisp < 20 || (elapsed < 300 && totalDisp < 28)) {

                        this.performRaycastClick(e.clientX, e.clientY);

                    }

                }

            });



            // 4. CLICK FALLBACK: Đảm bảo click trực tiếp luôn kích hoạt mở bảng thông tin

            this.container.addEventListener('click', (e) => {

                if (e.target && e.target.closest && e.target.closest('#office3dCharPopup')) {

                    return;

                }

                const existing = document.getElementById('office3dCharPopup');

                if (!existing) {

                    this.performRaycastClick(e.clientX, e.clientY);

                }

            });



            this.container.addEventListener('pointercancel', (e) => {

                this.isDragging = false;

                this.container.style.cursor = 'grab';

            });



            window.addEventListener('mouseup', () => {

                this.isDragging = false;

                if (this.container) this.container.style.cursor = 'grab';

            });



            window.addEventListener('blur', () => {

                this.isDragging = false;

                if (this.container) this.container.style.cursor = 'grab';

            });



            // 4. ZOOM IN / OUT: TĂNG THÊM 2 LẦN ZOOM (Min radius từ 16 giảm xuống 7, max radius 68)

            this.container.addEventListener('wheel', (e) => {

                e.preventDefault();

                const zoomDelta = e.deltaY * 0.035;

                this.cameraRadius += zoomDelta;

                this.cameraRadius = Math.max(7, Math.min(68, this.cameraRadius));

                this.updateCameraPosition();

            }, { passive: false });



            window.addEventListener('resize', () => this.handleResize());

        }



        handleResize() {

            if (!this.container || !this.renderer || !this.camera) return;

            const w = this.container.clientWidth;

            const h = this.container.clientHeight;

            if (w > 0 && h > 0) {

                this.camera.aspect = w / h;

                this.camera.updateProjectionMatrix();

                this.renderer.setSize(w, h);

            }

        }



        updateCameraPosition() {

            if (!this.camera) return;

            const x = this.cameraTarget.x + this.cameraRadius * Math.sin(this.cameraAngleH) * Math.cos(this.cameraAngleV);

            const y = this.cameraTarget.y + this.cameraRadius * Math.sin(this.cameraAngleV);

            const z = this.cameraTarget.z + this.cameraRadius * Math.cos(this.cameraAngleH) * Math.cos(this.cameraAngleV);

            this.camera.position.set(x, y, z);

            this.camera.lookAt(this.cameraTarget);

        }



        resetCamera() {

            this.cameraRadius = 38;

            this.cameraAngleH = Math.PI / 4 + 0.12;

            this.cameraAngleV = Math.PI / 5.2;

            this.cameraTarget.set(0, 1.5, 0);

            this.updateCameraPosition();

        }



        showCharacterPopup(data) {

            const existing = document.getElementById('office3dCharPopup');

            if (existing) existing.remove();



            const popup = document.createElement('div');

            popup.id = 'office3dCharPopup';

            popup.className = 'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border-2 border-[#004b93] p-5 w-[90%] max-w-[440px] z-50 text-slate-800 transition-all animate-in fade-in zoom-in-95 duration-200 select-none';



            // Chặn triệt để sự kiện lan truyền lên Three.js Canvas / Container

            // Đảm bảo thao tác bấm nút không bao giờ kích hoạt lại raycaster mở lại popup!

            ['pointerdown', 'pointerup', 'pointermove', 'mousedown', 'mouseup', 'click', 'dblclick'].forEach(evt => {

                popup.addEventListener(evt, (e) => {

                    e.stopPropagation();

                });

            });



            const char = data.charData || {};

            const asst = data.asst || {};

            const folderCount = (asst.drive_folder_ids && asst.drive_folder_ids.length) || 0;



            const close = (e) => {

                if (e) {

                    e.preventDefault();

                    e.stopPropagation();

                }

                popup.remove();

            };



            if (data.isCIO) {

                popup.innerHTML = `

                    <div class="flex items-start justify-between border-b border-slate-200 pb-3 mb-3">

                        <div class="flex items-center space-x-3">

                            <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-md border bg-gradient-to-br from-[#004b93] to-[#002855] text-white">

                                👑

                            </div>

                            <div>

                                <h3 class="text-base font-bold text-[#002855] leading-tight">${data.assistantName}</h3>

                                <p class="text-xs text-amber-700 font-semibold mt-0.5">Vị trí: <b>Tổng Giám Đốc (CIO)</b> — Điều hành Chiến lược AI</p>

                            </div>

                        </div>

                        <button id="closePopupBtn" type="button" class="cursor-pointer w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-800 hover:bg-slate-100 active:bg-slate-200 transition text-lg relative z-10" title="Đóng">

                            <i class="fa-solid fa-xmark pointer-events-none"></i>

                        </button>

                    </div>

                    <div class="space-y-2.5 text-xs text-slate-600 mb-4 select-text">

                        <p class="bg-blue-50/70 p-2.5 rounded-lg border border-blue-200 text-slate-800 leading-relaxed">

                            <b>Nhiệm vụ:</b> ${asst.description || data.role || 'Lãnh đạo toàn diện hệ thống AI, chỉ đạo chiến lược thuế và điều phối đội ngũ trợ lý chuyên môn.'}

                        </p>

                        <div class="flex items-center justify-between text-[11px] px-1 bg-slate-50 p-2 rounded-lg border border-slate-200">

                            <span><i class="fa-solid fa-users text-blue-600 mr-1"></i> Điều hành: <b>Toàn bộ Trợ lý & Thư ký</b></span>

                            <span><i class="fa-solid fa-brain text-amber-500 mr-1"></i> Mô hình: <b>Gemini 3.5 Pro Strategic</b></span>

                        </div>

                    </div>

                    <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100 flex-wrap gap-y-1.5">

                        <button id="cioMeetingBtn" type="button" class="cursor-pointer px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10" title="Kêu gọi toàn bộ trợ lý họp giao ban tại bàn họp">

                            <i class="fa-solid fa-people-group pointer-events-none"></i>

                            <span>Họp giao ban</span>

                        </button>

                        <button id="cioBdayBtn" type="button" class="cursor-pointer px-3.5 py-1.5 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10" title="Bật/tắt đèn và chúc mừng sinh nhật">

                            <i class="fa-solid fa-cake-candles pointer-events-none"></i>

                            <span>Sinh nhật</span>

                        </button>

                        <button id="closePopupBtn2" type="button" class="cursor-pointer px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 active:bg-slate-200 rounded-lg font-medium transition relative z-10">Đóng</button>

                    </div>

                `;



                this.container.appendChild(popup);

                popup.querySelector('#closePopupBtn').onclick = close;

                popup.querySelector('#closePopupBtn2').onclick = close;

                popup.querySelector('#cioMeetingBtn').onclick = (e) => {

                    close(e);

                    this.startMeeting();

                };

                popup.querySelector('#cioBdayBtn').onclick = (e) => {

                    close(e);

                    this.toggleLightsAndBirthday();

                };

                return;

            }



            if (data.isChiefSecretary) {

                const chiefCfg = data.chiefConfig || window.__lastChiefConfig || {};

                popup.innerHTML = `

                    <div class="flex items-start justify-between border-b border-pink-200 pb-3 mb-3">

                        <div class="flex items-center space-x-3">

                            <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-md border border-pink-300" style="background: linear-gradient(135deg, #f472b6, #db2777); color: white;">

                                🌸

                            </div>

                            <div>

                                <h3 class="text-base font-bold text-[#be185d] leading-tight">${data.name || chiefCfg.secretary_name || 'Tổng thư ký Cô Tấm'}</h3>

                                <p class="text-xs text-pink-700 font-semibold mt-0.5">Nhân vật độc lập: <b>${data.role || chiefCfg.secretary_role || 'Thư ký Nhắc việc & Lịch trình'}</b></p>

                            </div>

                        </div>

                        <button id="closePopupBtn" type="button" class="cursor-pointer w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition text-lg relative z-10" title="Đóng">

                            <i class="fa-solid fa-xmark pointer-events-none"></i>

                        </button>

                    </div>

                    <div class="space-y-2.5 text-xs text-slate-600 mb-4 select-text">

                        <div class="bg-pink-50/80 p-2.5 rounded-lg border border-pink-200 text-slate-800 leading-relaxed">

                            <b class="text-pink-900"><i class="fa-solid fa-crown text-amber-500 mr-1"></i>Vai trò chỉ đạo:</b>

                            <p class="mt-0.5 text-slate-700 font-medium">${data.role || chiefCfg.secretary_role || 'Thư ký Nhắc việc & Lịch trình'}</p>

                        </div>

                        <div class="bg-amber-50/80 p-2.5 rounded-lg border border-amber-200 text-amber-950 text-[11px] leading-relaxed">

                            <b class="text-amber-800"><i class="fa-solid fa-wand-magic-sparkles text-amber-600 mr-1"></i>Đặc điểm nhận diện 3D:</b>

                            <p class="mt-0.5 text-slate-700 font-medium">${chiefCfg.secretary_appearance || 'Nữ tổng thư ký dịu dàng, áo tứ thân lụa hồng cánh sen, tóc dài thướt tha cài hoa sen, đội nón quai thao, nói giọng nữ tiếng việt miền nam.'}</p>

                        </div>

                        <div class="flex items-center justify-between text-[11px] px-1 bg-slate-50 p-2 rounded-lg border border-slate-200">

                            <span><i class="fa-solid fa-bell text-rose-500 mr-1"></i> Lịch nhắc: <b>07:00 & 21:00</b></span>

                            <span><i class="fa-solid fa-volume-high text-pink-600 mr-1"></i> Giọng nữ miền Nam</span>

                        </div>

                    </div>

                    <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100 flex-wrap gap-y-1.5">

                        <button id="chiefReportCalBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-lg shadow-2xs flex items-center space-x-1.5 transition relative z-10" title="Cô Tấm chỉ báo cáo lịch làm việc trong ngày trong Google Calendar">

                            <i class="fa-solid fa-calendar-day pointer-events-none"></i>

                            <span>Báo cáo lịch làm việc</span>

                        </button>

                        <button id="chiefReportTaskBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-2xs flex items-center space-x-1.5 transition relative z-10" title="Cô Tấm chỉ báo cáo các công việc trong ngày trong Google Tasks">

                            <i class="fa-solid fa-list-check pointer-events-none"></i>

                            <span>Báo cáo công việc</span>

                        </button>

                        <button id="chiefReportAllBtn" type="button" class="cursor-pointer px-3.5 py-1.5 bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10" title="Cô Tấm báo cáo toàn bộ lịch làm việc và công việc hôm nay">

                            <i class="fa-solid fa-bullhorn pointer-events-none"></i>

                            <span>Báo cáo tất cả</span>

                        </button>

                        <button id="chiefGoScheduleBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-[#004b93] text-xs font-bold rounded-lg transition flex items-center space-x-1 relative z-10" title="Xem lịch trình Google Calendar & Tasks">

                            <i class="fa-regular fa-calendar-check text-[#004b93] pointer-events-none"></i>

                            <span>Lịch trình & Việc</span>

                        </button>

                        <button id="chiefEditConfigBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition flex items-center space-x-1 relative z-10" title="Chỉnh sửa cấu hình Tổng thư ký">

                            <i class="fa-solid fa-sliders pointer-events-none"></i>

                            <span>Cấu hình</span>

                        </button>

                        <button id="closePopupBtn2" type="button" class="cursor-pointer px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg font-medium transition relative z-10">Đóng</button>

                    </div>

                `;

                this.container.appendChild(popup);

                popup.querySelector('#closePopupBtn').onclick = close;

                popup.querySelector('#closePopupBtn2').onclick = close;

                const triggerReport = (type) => {

                    close();

                    if (window.triggerCoTamReportFromApp) window.triggerCoTamReportFromApp(type);

                    else if (this.reportToCIOByCoTam) this.reportToCIOByCoTam();

                };

                if (popup.querySelector('#chiefReportCalBtn')) popup.querySelector('#chiefReportCalBtn').onclick = () => triggerReport('calendar');

                if (popup.querySelector('#chiefReportTaskBtn')) popup.querySelector('#chiefReportTaskBtn').onclick = () => triggerReport('tasks');

                if (popup.querySelector('#chiefReportAllBtn')) popup.querySelector('#chiefReportAllBtn').onclick = () => triggerReport('all');

                popup.querySelector('#chiefGoScheduleBtn').onclick = (e) => {

                    close(e);

                    if (window.navigateToMenu) window.navigateToMenu('chief_secretary_reminders');

                };

                popup.querySelector('#chiefEditConfigBtn').onclick = (e) => {

                    close(e);

                    if (window.navigateToMenu) window.navigateToMenu('chief_secretary_settings');

                };

                return;

            }



            if (data.isSecretary) {

                const sec = data.sec || (this.secretariesList && this.secretariesList.find(s => s.id === data.secretaryId)) || {};

                popup.innerHTML = `

                    <div class="flex items-start justify-between border-b border-slate-200 pb-3 mb-3">

                        <div class="flex items-center space-x-3">

                            <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-md border" style="background-color: ${char.color ? '#' + char.color.toString(16).padStart(6, '0') : '#dc2626'}; color: white;">

                                ${char.avatar || '📜'}

                            </div>

                            <div>

                                <h3 class="text-base font-bold text-[#991b1b] leading-tight">${data.secretaryName}</h3>

                                <p class="text-xs text-rose-800 font-semibold mt-0.5">Cổ tích: <b>${char.name || data.characterName}</b> (Thư ký AI Tin tức)</p>

                            </div>

                        </div>

                        <button id="closePopupBtn" type="button" class="cursor-pointer w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-800 hover:bg-slate-100 active:bg-slate-200 transition text-lg relative z-10" title="Đóng">

                            <i class="fa-solid fa-xmark pointer-events-none"></i>

                        </button>

                    </div>

                    <div class="space-y-2.5 text-xs text-slate-600 mb-4 select-text">

                        <p class="bg-rose-50/70 p-2.5 rounded-lg border border-rose-200 text-slate-800">

                            <b>Nhiệm vụ:</b> ${data.role || sec.role || 'Thư ký tin tức thời gian thực qua Gemini'}

                        </p>

                        ${(sec.appearance || data.appearance) ? `

                        <div class="bg-amber-50/80 p-2.5 rounded-lg border border-amber-200 text-amber-950 text-[11px] leading-relaxed">

                            <b class="text-amber-800"><i class="fa-solid fa-wand-magic-sparkles text-amber-600 mr-1"></i>Đặc điểm hình dạng 3D:</b>

                            <p class="mt-0.5 text-slate-700 font-medium">${sec.appearance || data.appearance}</p>

                        </div>

                        ` : ''}

                        <div class="flex items-center justify-between text-[11px] px-1 bg-slate-50 p-2 rounded-lg border border-slate-200">

                            <span><i class="fa-solid fa-clock text-amber-500 mr-1"></i> Giờ báo cáo: <b>${data.scheduledTime || sec.scheduled_time || '08:00'} hàng ngày</b></span>

                            <span><i class="fa-solid fa-file-word text-blue-600 mr-1"></i> Xuất file Word (.docx)</span>

                        </div>

                    </div>

                    <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100 flex-wrap gap-y-1.5">

                        <button id="editSecBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10" title="Chỉnh sửa thông tin và nhiệm vụ thư ký">

                            <i class="fa-solid fa-pen-to-square pointer-events-none"></i>

                            <span>Sửa</span>

                        </button>

                        <button id="viewSecReportBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 text-xs font-bold rounded-lg transition flex items-center space-x-1 relative z-10" title="Xem báo cáo tin tức gần nhất">

                            <i class="fa-solid fa-file-lines text-sky-600 pointer-events-none"></i>

                            <span>Xem báo cáo</span>

                        </button>

                        <button id="requestSecReportBtn" type="button" class="cursor-pointer px-3.5 py-1.5 bg-[#004b93] hover:bg-[#002855] active:bg-[#001e3d] text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10" title="Yêu cầu thư ký chạy tìm kiếm tin tức ngay">

                            <i class="fa-solid fa-bolt-lightning text-yellow-300 pointer-events-none"></i>

                            <span>Yêu cầu báo cáo</span>

                        </button>

                        <button id="closePopupBtn2" type="button" class="cursor-pointer px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 active:bg-slate-200 rounded-lg font-medium transition relative z-10">Đóng</button>

                    </div>

                `;



                this.container.appendChild(popup);



                popup.querySelector('#closePopupBtn').onclick = close;

                popup.querySelector('#closePopupBtn2').onclick = close;

                popup.querySelector('#editSecBtn').onclick = (e) => {

                    close(e);

                    const secObj = data.sec || (this.secretariesList && this.secretariesList.find(s => s.id === data.secretaryId)) || {

                        id: data.secretaryId,

                        name: data.secretaryName,

                        character: data.characterName,

                        role: data.role,

                        scheduled_time: data.scheduledTime

                    };

                    if (this.onEditSecretary) this.onEditSecretary(secObj);

                };

                popup.querySelector('#viewSecReportBtn').onclick = (e) => {

                    close(e);

                    if (this.onSelectSecretary) this.onSelectSecretary(data.secretaryId);

                };

                popup.querySelector('#requestSecReportBtn').onclick = (e) => {

                    close(e);

                    if (this.onRequestSecretaryReport) this.onRequestSecretaryReport(data.secretaryId);

                };

                return;

            }



            popup.innerHTML = `

                <div class="flex items-start justify-between border-b border-slate-200 pb-3 mb-3">

                    <div class="flex items-center space-x-3">

                        <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-md border" style="background-color: ${char.color ? '#' + char.color.toString(16).padStart(6, '0') : '#0284c7'}; color: white;">

                            ${char.avatar || '🐱'}

                        </div>

                        <div>

                            <h3 class="text-base font-bold text-[#003b73] leading-tight">${data.assistantName}</h3>

                            <p class="text-xs text-amber-700 font-semibold mt-0.5">Nhân vật: <b>${char.name}</b> (${char.badge || 'Trợ lý'})</p>

                        </div>

                    </div>

                    <button id="closePopupBtn" type="button" class="cursor-pointer w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-800 hover:bg-slate-100 active:bg-slate-200 transition text-lg relative z-10" title="Đóng">

                        <i class="fa-solid fa-xmark pointer-events-none"></i>

                    </button>

                </div>

                <div class="space-y-2.5 text-xs text-slate-600 mb-4 select-text">

                    <p class="bg-slate-50 p-2.5 rounded-lg border border-slate-200">

                        <b>Nhiệm vụ:</b> ${asst.description || data.role || 'Trợ lý chuyên môn'}

                    </p>

                    <div class="flex items-center justify-between text-[11px] px-1 bg-slate-50 p-2 rounded-lg border border-slate-200">

                        <span><i class="fa-solid fa-folder-tree text-amber-500 mr-1"></i> Google Drive: <b>${folderCount} thư mục</b></span>

                        <span><i class="fa-solid fa-robot text-blue-500 mr-1"></i> Mô hình: <b>${asst.model || 'Gemini 3.5'}</b></span>

                    </div>

                </div>

                <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100 flex-wrap gap-y-1.5">

                    <button id="editAsstBtn" type="button" class="cursor-pointer px-3 py-1.5 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10" title="Chỉnh sửa thông tin trợ lý">

                        <i class="fa-solid fa-pen-to-square pointer-events-none"></i>

                        <span>Sửa</span>

                    </button>

                    <button id="chatNowBtn" type="button" class="cursor-pointer px-4 py-1.5 bg-[#004b93] hover:bg-[#003b73] active:bg-[#002855] text-white text-xs font-bold rounded-lg shadow-sm flex items-center space-x-1.5 transition relative z-10">

                        <i class="fa-solid fa-comments pointer-events-none"></i>

                        <span>Trò chuyện ngay</span>

                    </button>

                    <button id="closePopupBtn2" type="button" class="cursor-pointer px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 active:bg-slate-200 rounded-lg font-medium transition relative z-10">Đóng</button>

                </div>

            `;



            this.container.appendChild(popup);

            popup.querySelector('#closePopupBtn').onclick = close;

            popup.querySelector('#closePopupBtn2').onclick = close;

            popup.querySelector('#editAsstBtn').onclick = (e) => {

                close(e);

                const asstObj = data.asst || { id: data.assistantId, name: data.assistantName };

                if (this.onEditAssistant) this.onEditAssistant(asstObj);

            };

            popup.querySelector('#chatNowBtn').onclick = (e) => {

                close(e);

                if (this.onSelectAssistant) this.onSelectAssistant(data.assistantId);

            };

        }



        cleanup() {

            if (this.animationFrameId) {

                cancelAnimationFrame(this.animationFrameId);

                this.animationFrameId = null;

            }

            if (this.renderer && this.renderer.domElement && this.renderer.domElement.parentNode) {

                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);

            }

            this.characters = [];

            this.clickableObjects = [];

            this.takeCopterPropellers = [];

            this.nobita = null;

        }

    }



    // =========================================================================

    // 15. EXPOSE CONTROLLER GLOBALLY

    // =========================================================================

    window.DoraemonOfficeController = {

        instance: null,

        init: function (containerId, assistants, onSelectAssistant, secretaries, onSelectSecretary, onRequestSecretaryReport, onEditSecretary, onEditAssistant, chiefSecretary = null) {

            if (!this.instance) {

                this.instance = new Office3D(containerId, onSelectAssistant, onSelectSecretary, onRequestSecretaryReport, onEditSecretary, onEditAssistant);

            } else {

                this.instance.containerId = containerId;

                this.instance.container = document.getElementById(containerId);

                if (onSelectAssistant) this.instance.onSelectAssistant = onSelectAssistant;

                if (onSelectSecretary) this.instance.onSelectSecretary = onSelectSecretary;

                if (onRequestSecretaryReport) this.instance.onRequestSecretaryReport = onRequestSecretaryReport;

                if (onEditSecretary) this.instance.onEditSecretary = onEditSecretary;

                if (onEditAssistant) this.instance.onEditAssistant = onEditAssistant;

            }

            this.instance.init(assistants, secretaries, chiefSecretary);

            return this.instance;

        },

        updateAssistants: function (assistants, secretaries, chiefSecretary = null) {

            if (this.instance) this.instance.buildAssistants(assistants, secretaries, chiefSecretary);

        },

        resetCamera: function () {

            if (this.instance) this.instance.resetCamera();

        },

        resize: function () {

            if (this.instance) this.instance.handleResize();

        },

        togglePlay: function () {

            if (this.instance && this.instance.audioPlayer) this.instance.audioPlayer.togglePlay();

        },

        selectTrack: function (trackIdx) {

            if (this.instance && this.instance.audioPlayer) this.instance.audioPlayer.selectTrack(trackIdx);

        },

        toggleMute: function () {

            if (this.instance && this.instance.audioPlayer) this.instance.audioPlayer.toggleMute();

        },

        setVolume: function (vol) {

            if (this.instance && this.instance.audioPlayer) this.instance.audioPlayer.setVolume(vol);

        },

        triggerWork: function (asstId) {

            if (this.instance) this.instance.triggerAssistantWork(asstId);

        },

        finishWork: function (asstId) {

            if (this.instance) this.instance.finishAssistantWork(asstId);

        },

        reportToCIOByCoTam: function (speechText, onDone) {

            if (this.instance) return this.instance.reportToCIOByCoTam(speechText, onDone);

        },

        toggleVoiceMute: function () {

            if (this.instance) return this.instance.toggleVoiceMute();

        },

        setVoiceMute: function (muted) {

            if (this.instance) this.instance.setVoiceMute(muted);

        },

        startMeeting: function () {

            if (this.instance) this.instance.startMeeting();

        },

        playSelectedVideo: function () {

            const sel = document.getElementById('officeVideoSelect');

            const videoId = sel ? sel.value : '3S6R-nOA2eY';

            if (this.instance) this.instance.playVideo(videoId);

        },

        stopVideo: function () {

            if (this.instance) this.instance.stopVideo();

        },

        onVideoSelectChange: function (videoId) {

            if (this.instance && this.instance.isVideoPlaying) {

                this.instance.playVideo(videoId);

            }

        },

        setTheme: function (themeName) {

            if (this.instance) this.instance.setTheme(themeName);

        },

        toggleLightsAndBirthday: function () {

            if (this.instance) this.instance.toggleLightsAndBirthday();

        }

    };



})();

