import api from './axios';

export const authService = {
  login: async (email: string, senha: string) => {
    const response = await api.post('/api/login', { email, senha });
    if (response.data.token) {
      localStorage.setItem('mediary_token', response.data.token);
    }
    return response.data;
  },
  cadastro: async (nome: string, email: string, senha: string) => {
    const response = await api.post('/api/cadastro', { nome, email, senha });
    return response.data;
  },
  logout: async () => {
    localStorage.removeItem('mediary_token');
    return { message: 'Logout realizado com sucesso' };
  },
  me: async () => {
    const response = await api.get('/api/me');
    return response.data;
  },
  updatePerfil: async (nome: string, email: string) => {
    const response = await api.put('/api/usuario', { nome, email });
    return response.data;
  },
  updateSenha: async (senha_atual: string, senha_nova: string) => {
    const response = await api.put('/api/usuario/senha', { senha_atual, senha_nova });
    return response.data;
  }
};
