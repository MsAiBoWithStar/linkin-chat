/**
 * LinkIn 前端入口
 */
const API_BASE = '/api';

// 全局 Toast 通知
function showToast(message, type = 'success', duration = 3000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${type === 'success' ? '✓' : '⚠'}</span>
    <span class="toast-message">${message}</span>
  `;
  container.appendChild(toast);
  
  // 触发动画
  setTimeout(() => toast.classList.add('show'), 10);
  
  // 自动移除
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => container.removeChild(toast), 300);
  }, duration);
}

// API 客户端 - 统一处理HTTP请求和认证
class APIClient {
  constructor(baseURL = API_BASE) {
    this.baseURL = baseURL;
  }

  getToken() {
    return localStorage.getItem('linkin_token');
  }

  setToken(token) {
    if (token) {
      localStorage.setItem('linkin_token', token);
    } else {
      localStorage.removeItem('linkin_token');
    }
  }

  async request(method, url, data) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    const token = this.getToken();
    if (token) opts.headers['Authorization'] = 'Bearer ' + token;
    if (data && (method === 'POST' || method === 'PUT')) {
      opts.body = JSON.stringify(data);
    }
    try {
      const response = await fetch(this.baseURL + url, opts);
      return await response.json();
    } catch (error) {
      return { code: -1, message: '网络错误', error };
    }
  }

  async uploadFile(file) {
    const form = new FormData();
    form.append('file', file);
    const token = this.getToken();
    const opts = { method: 'POST', body: form };
    if (token) opts.headers = { 'Authorization': 'Bearer ' + token };
    try {
      const response = await fetch(this.baseURL + '/upload', opts);
      return await response.json();
    } catch (error) {
      return { code: -1, message: '网络错误', error };
    }
  }
}

// 全局 API 客户端实例
const api = new APIClient();

// 兼容旧的全局函数调用
function request(method, url, data) {
  return api.request(method, url, data);
}

function uploadFile(file) {
  return api.uploadFile(file);
}

// 消息工具集合
const MessageUtils = {
  isImageFile(filename) {
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'];
    const ext = (filename || '').toLowerCase().split('.').pop();
    return imageExts.includes(ext);
  },
  getFileUrl(fileInfo) {
    if (!fileInfo || !fileInfo.file_path) return '';
    return fileInfo.file_path.startsWith('http') ? fileInfo.file_path : ('/storage/' + fileInfo.file_path);
  },
  downloadFile(fileInfo) {
    if (!fileInfo || !fileInfo.file_path) return;
    const url = this.getFileUrl(fileInfo);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileInfo.file_name || 'download';
    a.click();
  },
  viewImage(fileInfo) {
    if (!fileInfo || !this.isImageFile(fileInfo.file_name)) return;
    const url = this.getFileUrl(fileInfo);
    // 简单实现：新窗口打开
    window.open(url, '_blank');
  }
};

const { createApp } = Vue;

createApp({
  data() {
    return {
      currentUser: null,
      token: null,
      lang: localStorage.getItem('linkin_lang') || 'zh',
      i18n: {},
      showLogin: false,
      showRegister: false,
      generatedLinkId: '',
      showAddFriend: false,
      showCreateGroup: false,
      showInviteModal: false,
      showKickModal: false,
      showGroupMembers: false,
      showDissolveModal: false,
      showDeleteFriendModal: false,
      deleteFriendTarget: null,
      deleteFriendClearHistory: false,
      showUserMenu: false,
      showLangMenu: false,
      showSettingsModal: false,
      settingsForm: { nickname: '', avatar: '' },
      avatarCacheBuster: Date.now(),
      avatarUploading: false,
      avatarUploadSuccess: false,
      showSearchModal: false,
      searchQuery: '',
      searchResults: [],
      searchQueried: false,
      createGroupName: '',
      createGroupMemberIds: [],
      groupMembers: [],
      inviteCandidateFriends: [],
      inviteSelectedIds: [],
      kickCandidateMembers: [],
      kickSelectedIds: [],
      leftTab: 'chats',
      friends: [],
      groups: [],
      unreadMap: {},  // key: 'user_2' | 'group_1', value: unread count
      chatList: [],
      currentChat: null,
      messages: [],
      inputText: '',
      form: { nickname: '', link_id: '', password: '', confirm_password: '' },
      searchKeyword: '',
      friendSearchResults: [],
      friendSearchQueried: false,
      socket: null,
    };
  },
  mounted() {
    this.token = localStorage.getItem('linkin_token');
    this.setLanguage(this.lang);
    if (this.token) this.fetchMe();
    // 点击外部关闭用户菜单
    document.addEventListener('click', (e) => {
      const trigger = document.querySelector('.user-menu-trigger');
      if (trigger && !trigger.contains(e.target)) {
        this.showUserMenu = false;
      }
    });
    // 生成通讯码
    this.generateLinkId();
  },
  computed: {
    displayMessages() {
      if (!this.messages || this.messages.length === 0) return [];
      const result = [];
      const GAP = 5 * 60 * 1000; // 5分钟
      this.messages.forEach((msg, idx) => {
        const prev = idx > 0 ? this.messages[idx - 1] : null;
        const gap = prev ? (new Date(msg.created_at) - new Date(prev.created_at)) : Infinity;
        // 超过5分钟间隔或第一条，插入时间线
        if (!prev || gap > GAP) {
          result.push({ _type: 'time', _id: 'ts-' + idx, time: msg.created_at });
        }
        // 始终显示头像（简化逻辑，避免头像显示问题）
        const showAvatar = true;
        result.push(Object.assign({}, msg, { _type: 'msg', showAvatar }));
      });
      return result;
    }
  },
  methods: {
    avatarUrl(path) {
      if (!path) return '';
      if (path.startsWith('http')) return path;
      // 使用缓存破坏参数，只在更新头像时改变
      return '/storage/' + path + '?v=' + this.avatarCacheBuster;
    },
    t(key, params) {
      const dict = this.i18n && this.i18n[this.lang] ? this.i18n[this.lang] : {};
      let text = dict[key] || key;
      if (!params) return text;
      return text.replace(/\{(\w+)\}/g, (m, k) => (params[k] != null ? params[k] : ''));
    },
    hideLangMenuDelay() {
      setTimeout(() => { this.showLangMenu = false; }, 150);
    },
    async setLanguage(lang) {
      this.showLangMenu = false;
      const map = { zh: 'chinese', en: 'english' };
      const filename = map[lang] || 'chinese';
      try {
        const res = await fetch('/static/i18n/' + filename + '.json');
        const data = await res.json();
        this.i18n = { ...this.i18n, [lang]: data };
        this.lang = lang;
        localStorage.setItem('linkin_lang', lang);
        if (data['app.title']) document.title = data['app.title'];
        document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN';
      } catch (err) {
        // fallback: keep existing language
      }
    },
    async markChatRead(chatType, chatId) {
      if (!chatType || !chatId) return;
      await request('POST', '/messages/read', {
        chat_type: chatType,
        chat_id: chatId,
      });
      const key = (chatType === 'group' ? 'group_' : 'user_') + chatId;
      if (this.unreadMap[key]) {
        this.unreadMap = { ...this.unreadMap, [key]: 0 };
      }
    },
    async _sendMessage(payload) {
      /**
       * 统一的消息发送函数
       * payload: { content } 或 { file_path, file_name }
       */
      if (!this.currentChat) return null;
      
      let url, reqData;
      if (this.currentChat.type === 'group') {
        url = '/messages/group';
        reqData = { group_id: this.currentChat.id, ...payload };
      } else {
        url = '/messages/private';
        reqData = { to_user: this.currentChat.id, ...payload };
      }
      
      const res = await request('POST', url, reqData);
      if (res.code !== 0) {
        showToast(res.message || this.t('toast.sendFail'), 'error');
        return null;
      }
      
      // 添加消息到列表（如果尚未存在）
      if (res.data && !this.messages.some(m => m.id === res.data.id)) {
        this.messages.push(res.data);
      }
      
      this.$nextTick(() => this.scrollToBottom());
      return res.data;
    },
    async fetchMe() {
      const res = await request('GET', '/me');
      if (res.code === 0 && res.data) {
        this.currentUser = res.data;
        this.settingsForm.nickname = res.data.nickname;
        this.settingsForm.avatar = res.data.avatar;
        this.loadFriends();
        this.loadGroups();
        this.loadUnreadSummary();
        this.connectSocket();
      } else {
        this.logout();
      }
    },
    async loadFriends() {
      const res = await request('GET', '/friends');
      if (res.code === 0) this.friends = res.data || [];
    },
    async loadGroups() {
      const res = await request('GET', '/groups');
      if (res.code === 0) this.groups = res.data || [];
    },
    async loadUnreadSummary() {
      const res = await request('GET', '/messages/unread-summary');
      if (res.code !== 0 || !res.data) return;
      const map = {};
      for (const it of res.data) {
        const key = (it.chat_type === 'group' ? 'group_' : 'user_') + it.chat_id;
        map[key] = it.unread;
      }
      this.unreadMap = map;
    },
    connectSocket() {
      if (this.socket) return;
      this.socket = io(location.origin, { 
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5
      });
      
      this.socket.on('connect', () => {
        this.socket.emit('authenticate', { token: this.token });
      });
      
      this.socket.on('authenticated', (data) => {
      });
      
      this.socket.on('auth_fail', (data) => {
        showToast(this.t('toast.realtimeFail'), 'error');
      });
      
      this.socket.on('disconnect', (reason) => {
      });
      
      this.socket.on('connect_error', (error) => {
      });
      
      this.socket.on('new_message', (msg) => {
        const isPrivate = msg.receiver_id != null;
        const isReceiver = isPrivate
          ? msg.receiver_id === this.currentUser.id
          : msg.sender_id !== this.currentUser.id;
        // 判断消息是否属于当前聊天
        const isCurrent = this.currentChat && (
          (isPrivate && this.currentChat.type === 'user' && 
            ((msg.sender_id === this.currentUser.id && msg.receiver_id === this.currentChat.id) ||
             (msg.sender_id === this.currentChat.id && msg.receiver_id === this.currentUser.id))) ||
          (!isPrivate && msg.group_id === this.currentChat?.id)
        );
        if (isCurrent) {
          // 检查消息是否已存在（防止重复）
          if (!this.messages.some(m => m.id === msg.id)) {
            this.messages.push(msg);
            this.$nextTick(() => this.scrollToBottom());
          }
          if (isReceiver) {
            this.markChatRead(this.currentChat.type, this.currentChat.id);
          }
        } else {
          // 仅有接收者才计入未读，发送者的消息不计入未读
          if (isReceiver) {
            const key = isPrivate ? ('user_' + msg.sender_id) : ('group_' + msg.group_id);
            this.unreadMap = { ...this.unreadMap, [key]: (this.unreadMap[key] || 0) + 1 };
          }
        }
      });
      
      this.socket.on('friend_added', (data) => {
        if (data.message) {
          showToast(data.message, 'success');
        }
        // 刷新好友列表
        this.loadFriends();
      });
      
      this.socket.on('friend_removed', (data) => {
        // 刷新好友列表
        this.loadFriends();
        // 如果正在和被删除的好友聊天，清空当前聊天
        if (this.currentChat && this.currentChat.type === 'user' && this.currentChat.id === data.friend_id) {
          this.currentChat = null;
          this.messages = [];
          showToast(this.t('toast.friendRemoved'), 'error');
        }
      });

      this.socket.on('profile_updated', (data) => {
        const updated = data && data.user;
        if (!updated) return;
        if (this.currentUser && updated.id === this.currentUser.id) {
          this.currentUser = { ...this.currentUser, nickname: updated.nickname, avatar: updated.avatar };
          this.settingsForm.nickname = updated.nickname;
          this.settingsForm.avatar = updated.avatar;
          this.avatarCacheBuster = Date.now();
        }
        this.friends = (this.friends || []).map(f => (
          f.id === updated.id ? { ...f, nickname: updated.nickname, avatar: updated.avatar, link_id: updated.link_id } : f
        ));
        if (this.currentChat && this.currentChat.type === 'user' && this.currentChat.id === updated.id) {
          const name = updated.nickname + (updated.link_id ? ('(' + updated.link_id + ')') : '');
          this.currentChat = { ...this.currentChat, name, avatar: updated.avatar };
        }
        if (this.messages && this.messages.length) {
          this.messages = this.messages.map(m => (
            m.sender_id === updated.id && m.sender
              ? { ...m, sender: { ...m.sender, nickname: updated.nickname, avatar: updated.avatar } }
              : m
          ));
        }
      });

      this.socket.on('group_added', (data) => {
        if (data && data.message) showToast(data.message, 'success');
        this.loadGroups();
      });

      this.socket.on('group_removed', (data) => {
        if (data && data.message) showToast(data.message, 'error');
        this.loadGroups();
        if (this.currentChat && this.currentChat.type === 'group' && data && data.group_id === this.currentChat.id) {
          this.closeChat();
        }
      });
    },
    generateLinkId() {
      // 生成8位数字通讯码
      this.generatedLinkId = String(Math.floor(10000000 + Math.random() * 90000000));
    },
    resetAuthForm() {
      this.form = { nickname: '', link_id: '', password: '', confirm_password: '' };
    },
    openRegisterModal() {
      this.generateLinkId();
      this.resetAuthForm();
      this.showRegister = true;
      this.showLogin = false;
    },
    openLoginModal() {
      this.resetAuthForm();
      this.showLogin = true;
      this.showRegister = false;
    },
    async register() {
      if (!this.form.nickname || !this.form.nickname.trim()) {
        showToast(this.t('toast.inputNickname'), 'error');
        return;
      }
      if (!this.form.password) {
        showToast(this.t('toast.inputPassword'), 'error');
        return;
      }
      if (this.form.password !== this.form.confirm_password) {
        showToast(this.t('toast.passwordMismatch'), 'error');
        return;
      }
      const res = await request('POST', '/register', {
        nickname: this.form.nickname,
        link_id: this.generatedLinkId,
        password: this.form.password,
      });
      if (res.code !== 0) {
        showToast(res.message || this.t('toast.registerFail'), 'error');
        return;
      }
      this.token = res.data.token;
      localStorage.setItem('linkin_token', this.token);
      this.currentUser = res.data.user;
      this.showRegister = false;
      this.resetAuthForm();
      showToast(this.t('toast.registerSuccess', { linkId: this.generatedLinkId }), 'success', 5000);
      this.loadFriends();
      this.loadGroups();
      this.loadUnreadSummary();
      this.connectSocket();
    },
    async login() {
      if (!this.form.link_id || this.form.link_id.length !== 8) {
        showToast(this.t('toast.inputLinkId'), 'error');
        return;
      }
      if (!this.form.password) {
        showToast(this.t('toast.inputPassword'), 'error');
        return;
      }
      const res = await request('POST', '/login', {
        link_id: this.form.link_id,
        password: this.form.password,
      });
      if (res.code !== 0) {
        showToast(res.message || this.t('toast.loginFail'), 'error');
        return;
      }
      this.token = res.data.token;
      localStorage.setItem('linkin_token', this.token);
      this.currentUser = res.data.user;
      this.showLogin = false;
      this.resetAuthForm();
      showToast(this.t('toast.loginSuccess'), 'success');
      this.loadFriends();
      this.loadGroups();
      this.loadUnreadSummary();
      this.connectSocket();
    },
    logout() {
      this.token = null;
      this.currentUser = null;
      this.currentChat = null;
      this.messages = [];
      localStorage.removeItem('linkin_token');
      if (this.socket) this.socket.disconnect();
      this.socket = null;
    },
    isImageFile(m) {
      if (!m || !m.file_name) return false;
      const ext = m.file_name.split('.').pop().toLowerCase();
      return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext);
    },
    viewImage(m) {
      if (!m || !m.file_path) return;
      const url = this.fileDownloadUrl(m);
      window.open(url, '_blank');
    },
    async onAvatarSelected(ev) {
      const file = ev.target.files && ev.target.files[0];
      if (!file) return;
      this.avatarUploading = true;
      this.avatarUploadSuccess = false;
      try {
        const res = await uploadFile(file);
        if (res.code === 0 && res.data) {
          this.settingsForm.avatar = res.data.file_path;
          this.avatarUploadSuccess = true;
          showToast(this.t('toast.avatarUploaded'), 'success');
          // 3秒后重置成功标志
          setTimeout(() => { this.avatarUploadSuccess = false; }, 3000);
        } else {
          showToast(this.t('toast.uploadFail', { message: res.message || this.t('toast.unknownError') }), 'error');
        }
      } catch (err) {
        showToast(this.t('toast.uploadFail', { message: err.message }), 'error');
      } finally {
        this.avatarUploading = false;
      }
    },
    async saveSettings() {
      if (!this.settingsForm.nickname || !this.settingsForm.nickname.trim()) {
        showToast(this.t('toast.nicknameEmpty'), 'error');
        return;
      }
      const res = await request('PUT', '/profile', {
        nickname: this.settingsForm.nickname.trim(),
        avatar: this.settingsForm.avatar || ''
      });
      if (res.code === 0) {
        // 更新昵称和头像
        this.currentUser.nickname = this.settingsForm.nickname.trim();
        this.currentUser.avatar = this.settingsForm.avatar;
        // 更新缓存破坏参数，强制重新加载头像
        this.avatarCacheBuster = Date.now();
        this.$forceUpdate();
        this.showSettingsModal = false;
        showToast(this.t('toast.settingsSaved'), 'success');
      } else {
        showToast(this.t('toast.settingsSaveFail', { message: res.message || this.t('toast.unknownError') }), 'error');
      }
    },
    async openChat(c) {
      if (this.currentChat && this.socket) {
        const prevKey = this.currentChat.key;
        if (prevKey && prevKey !== ((c.type || 'user') + '_' + c.id)) {
          this.socket.emit('leave_chat', { room: prevKey });
        }
      }
      this.currentChat = {
        type: c.type || 'user',
        id: c.id,
        name: c.name,
        avatar: c.avatar,
        owner_id: c.owner_id,
        key: (c.type || 'user') + '_' + c.id,
      };
      this.unreadMap = { ...this.unreadMap, [this.currentChat.key]: 0 };
      await this.loadMessages();
      this.socket && this.socket.emit('join_chat', { room: this.currentChat.key });
    },
    closeChat() {
      if (this.currentChat && this.socket) {
        this.socket.emit('leave_chat', { room: this.currentChat.key });
      }
      this.currentChat = null;
      this.messages = [];
      this.showDissolveModal = false;
    },
    async loadMessages() {
      if (!this.currentChat) return;
      let url;
      if (this.currentChat.type === 'group') {
        url = '/messages/group/' + this.currentChat.id;
      } else {
        url = '/messages/private/' + this.currentChat.id;
      }
      const res = await request('GET', url);
      this.messages = (res.code === 0 && res.data) ? res.data : [];
      await this.markChatRead(this.currentChat.type, this.currentChat.id);
      this.loadUnreadSummary();
      this.$nextTick(() => this.scrollToBottom());
    },
    scrollToBottom() {
      const el = this.$refs.messagesEl;
      if (el) el.scrollTop = el.scrollHeight;
    },
    async sendText() {
      const text = (this.inputText || '').trim();
      if (!text || !this.currentChat) return;
      const res = await this._sendMessage({ content: text });
      if (res) {
        this.inputText = '';
        this.$nextTick(() => {
          const el = this.$refs.messageInput;
          if (el) el.style.height = 'auto';
        });
      }
    },
    adjustTextareaHeight() {
      this.$nextTick(() => {
        const el = this.$refs.messageInput;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
      });
    },
    fileDownloadUrl(m) {
      return MessageUtils.getFileUrl(m);
    },
    downloadFile(m) {
      MessageUtils.downloadFile(m);
    },
    async onFileSelected(ev) {
      const file = ev.target.files && ev.target.files[0];
      if (!file || !this.currentChat) return;
      ev.target.value = '';
      const uploadRes = await uploadFile(file);
      if (uploadRes.code !== 0 || !uploadRes.data) {
        showToast(uploadRes.message || this.t('toast.uploadFailed'), 'error');
        return;
      }
      await this._sendMessage({
        file_path: uploadRes.data.file_path,
        file_name: uploadRes.data.file_name
      });
    },
    formatTime(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      const now = new Date();
      const locale = this.lang === 'en' ? 'en-US' : 'zh-CN';
      if (d.toDateString() === now.toDateString()) {
        return d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
      }
      return d.toLocaleDateString(locale, { month: '2-digit', day: '2-digit' }) + ' ' +
        d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
    },
    async createGroup() {
      const name = (this.createGroupName || '').trim();
      if (!name) {
        showToast(this.t('toast.groupNameRequired'), 'error');
        return;
      }
      const res = await request('POST', '/groups', { group_name: name, member_ids: this.createGroupMemberIds });
      if (res.code !== 0) {
        showToast(res.message || this.t('toast.createGroupFail'), 'error');
        return;
      }
      this.groups.push(res.data);
      this.showCreateGroup = false;
      this.createGroupName = '';
      this.createGroupMemberIds = [];
      this.openChat({ type: 'group', id: res.data.id, name: res.data.group_name, avatar: res.data.group_avatar, owner_id: res.data.owner_id });
    },
    async openGroupMembers() {
      if (!this.currentChat || this.currentChat.type !== 'group') return;
      const res = await request('GET', '/groups/' + this.currentChat.id + '/members');
      if (res.code === 0 && res.data) {
        this.groupMembers = res.data;
      } else {
        this.groupMembers = [];
        showToast(res.message || this.t('toast.loadGroupMembersFail'), 'error');
      }
      this.showGroupMembers = true;
    },
    async openInviteModal() {
      if (!this.currentChat || this.currentChat.type !== 'group') return;
      const res = await request('GET', '/groups/' + this.currentChat.id + '/members');
      if (res.code !== 0 || !res.data) return;
      const inGroupIds = new Set((res.data || []).map(m => m.user_id));
      this.inviteCandidateFriends = this.friends.filter(f => !inGroupIds.has(f.id));
      this.inviteSelectedIds = [];
      this.showInviteModal = true;
    },
    toggleInviteSelect(userId) {
      this.inviteSelectedIds = this.toggleInArray(userId, this.inviteSelectedIds);
    },
    async confirmInviteSelection() {
      if (!this.currentChat || this.currentChat.type !== 'group') return;
      if (!this.inviteSelectedIds.length) {
        showToast(this.t('toast.inviteSelectRequired'), 'error');
        return;
      }
      let success = 0;
      let firstError = '';
      for (const userId of this.inviteSelectedIds) {
        const res = await request('POST', '/groups/' + this.currentChat.id + '/invite', { user_id: userId });
        if (res.code === 0) {
          success += 1;
        } else if (!firstError) {
          firstError = res.message || this.t('toast.inviteFail');
        }
      }
      this.showInviteModal = false;
      this.inviteSelectedIds = [];
      this.groupMembers = [];
      if (firstError) {
        showToast(firstError, 'error');
      } else {
        showToast(this.t('toast.invitedCount', { count: success }), 'success');
      }
    },
    async openKickModal() {
      if (!this.currentChat || this.currentChat.type !== 'group') return;
      const res = await request('GET', '/groups/' + this.currentChat.id + '/members');
      if (res.code !== 0 || !res.data) return;
      this.groupMembers = res.data;
      this.kickCandidateMembers = res.data.filter(m => m.user_id !== this.currentUser.id && m.role !== 'owner');
      this.kickSelectedIds = [];
      this.showKickModal = true;
    },
    toggleKickSelect(userId) {
      this.kickSelectedIds = this.toggleInArray(userId, this.kickSelectedIds);
    },
    async confirmKickSelection() {
      if (!this.currentChat || this.currentChat.type !== 'group') return;
      if (!this.kickSelectedIds.length) {
        showToast(this.t('toast.kickSelectRequired'), 'error');
        return;
      }
      let success = 0;
      let firstError = '';
      for (const userId of this.kickSelectedIds) {
        const res = await request('POST', '/groups/' + this.currentChat.id + '/kick', { user_id: userId });
        if (res.code === 0) {
          success += 1;
        } else if (!firstError) {
          firstError = res.message || this.t('toast.kickFail');
        }
      }
      this.showKickModal = false;
      this.kickSelectedIds = [];
      this.kickCandidateMembers = [];
      if (firstError) {
        showToast(firstError || this.t('toast.kickFail'), 'error');
      } else {
        showToast(this.t('toast.kickedCount', { count: success }), 'success');
      }
    },
    async doSearch() {
      const q = (this.searchQuery || '').trim();
      if (!q) return;
      const res = await request('GET', '/messages/search?q=' + encodeURIComponent(q));
      this.searchResults = (res.code === 0 && res.data) ? res.data : [];
      this.searchQueried = true;
    },
    openChatFromSearch(m) {
      this.showSearchModal = false;
      this.searchResults = [];
      this.searchQueried = false;
      if (m.group_id) {
        const g = this.groups.find(x => x.id === m.group_id);
        this.openChat({ type: 'group', id: m.group_id, name: g ? g.group_name : (this.t('chat.groupShort') + m.group_id), avatar: g && g.group_avatar, owner_id: g && g.owner_id });
      } else {
        const otherId = m.sender_id === this.currentUser.id ? m.receiver_id : m.sender_id;
        const f = this.friends.find(x => x.id === otherId);
        const name = f ? (f.nickname + '(' + f.link_id + ')') : (this.t('chat.userShort') + otherId);
        this.openChat({ type: 'user', id: otherId, name, avatar: f && f.avatar });
      }
    },
    async confirmDissolveGroup() {
      if (!this.currentChat) return;
      const res = await request('POST', '/groups/' + this.currentChat.id + '/dissolve');
      if (res.code !== 0) {
        showToast(res.message || this.t('toast.dissolveFail'), 'error');
        return;
      }
      this.showDissolveModal = false;
      this.groups = this.groups.filter(g => g.id !== this.currentChat.id);
      this.currentChat = null;
      this.messages = [];
      this.loadUnreadSummary();
    },
    async searchFriend() {
      const kw = (this.searchKeyword || '').trim();
      if (!kw) return;
      this.friendSearchQueried = false;
      const res = await request('POST', '/friends/search', {
        link_id: /^\d{8}$/.test(kw) ? kw : undefined,
        nickname: /^\d{8}$/.test(kw) ? undefined : kw
      });
      this.friendSearchQueried = true;
      if (res.code === 0 && res.data) {
        // 过滤掉自己
        this.friendSearchResults = res.data.filter(u => u.id !== this.currentUser.id);
      } else {
        this.friendSearchResults = [];
      }
    },
    async addFriendById(user) {
      const addRes = await request('POST', '/friends/add', { friend_id: user.id });
      if (addRes.code === 0) {
        this.friends.push(user);
        showToast(this.t('toast.addFriendSuccess', { name: user.nickname }), 'success');
      } else {
        showToast(addRes.message || this.t('toast.addFriendFail'), 'error');
      }
    },
    isFriendAlready(userId) {
      return this.friends.some(f => f.id === userId);
    },
    isGroupMemberSelected(userId) {
      return (this.createGroupMemberIds || []).includes(userId);
    },
    toggleInArray(id, array) {
      if (array.includes(id)) {
        return array.filter(item => item !== id);
      } else {
        return [...array, id];
      }
    },
    toggleGroupMember(userId) {
      this.createGroupMemberIds = this.toggleInArray(userId, this.createGroupMemberIds);
    },
    openDeleteFriendModal(friend) {
      this.deleteFriendTarget = friend;
      this.deleteFriendClearHistory = false;
      this.showDeleteFriendModal = true;
    },
    async confirmDeleteFriend() {
      if (!this.deleteFriendTarget) return;
      const res = await request('POST', '/friends/delete', { 
        friend_id: this.deleteFriendTarget.id,
        clear_history: this.deleteFriendClearHistory
      });
      if (res.code === 0) {
        this.friends = this.friends.filter(f => f.id !== this.deleteFriendTarget.id);
        this.showDeleteFriendModal = false;
        this.deleteFriendTarget = null;
        this.deleteFriendClearHistory = false;
        showToast(this.t('toast.deleteFriendSuccess'), 'success');
      } else {
        showToast(res.message || this.t('toast.deleteFriendFail'), 'error');
      }
    },
    buildChatList() {
      const u = (key) => this.unreadMap[key] || 0;
      this.chatList = [
        ...(this.friends || []).map(f => ({
          type: 'user',
          id: f.id,
          name: f.nickname,
          avatar: f.avatar,
          key: 'user_' + f.id,
          unread: u('user_' + f.id),
        })),
        ...(this.groups || []).map(g => ({
          type: 'group',
          id: g.id,
          name: g.group_name,
          avatar: g.group_avatar,
          owner_id: g.owner_id,
          key: 'group_' + g.id,
          unread: u('group_' + g.id),
        })),
      ];
    },
  },
  watch: {
    friends: { handler() { this.buildChatList(); }, deep: true },
    groups: { handler() { this.buildChatList(); }, deep: true },
    unreadMap: { handler() { this.buildChatList(); }, deep: true },
  },
}).mount('#app');
