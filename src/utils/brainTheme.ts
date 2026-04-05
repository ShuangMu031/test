import { BrainName } from '../types/trace';

export interface BrainTheme {
  primary: string;
  secondary: string;
  accent: string;
  text: string;
}

export const brainThemes: Record<BrainName, BrainTheme> = {
  emotion: {
    primary: '#FF6B6B',
    secondary: '#FF8787',
    accent: '#FFD166',
    text: '#FFFFFF'
  },
  memory: {
    primary: '#4ECDC4',
    secondary: '#7ED9D1',
    accent: '#45B7AA',
    text: '#FFFFFF'
  },
  world: {
    primary: '#45B7D1',
    secondary: '#71C7EC',
    accent: '#3498DB',
    text: '#FFFFFF'
  },
  npc: {
    primary: '#9B59B6',
    secondary: '#B39DDB',
    accent: '#8E44AD',
    text: '#FFFFFF'
  },
  behavior: {
    primary: '#27AE60',
    secondary: '#52C41A',
    accent: '#2ECC71',
    text: '#FFFFFF'
  },
  supervisor: {
    primary: '#F39C12',
    secondary: '#F9A826',
    accent: '#E67E22',
    text: '#FFFFFF'
  }
};

export const sceneThemes = {
  service: {
    primary: '#3498DB',
    secondary: '#2980B9',
    accent: '#1E88E5'
  },
  game: {
    primary: '#9B59B6',
    secondary: '#8E44AD',
    accent: '#7B2CBF'
  },
  companion: {
    primary: '#27AE60',
    secondary: '#229954',
    accent: '#2ECC71'
  }
};