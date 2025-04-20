import { createTheme } from '@mui/material/styles';

export const theme = {
  colors: {
    primary: '#2C3E4B',
    secondary: '#D4A321',
    text: '#7A7A7A',
    accent: '#61CE70',
    dark: '#2C3E4B',
    yellow: '#EEC966',
    gold: '#D4A321',
    black: '#000000',
    white: '#FFFFFF',
    transparent: '#02010100',
    primary80: '#2C3E4B80',
    darkBlue: '#3C4E58',
    teal: '#427473',
    lightGray: '#F1F3F5',
    primary80Alt: '#2C3E4B80',
    gray80: '#A2B1BA80'
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif'
  },
  palette: {
    background: {
      default: '#FFFFFF'
    },
    text: {
      primary: '#3C4E58'
    }
  }
};

export const cssVariables = {
  '--e-global-color-primary': theme.colors.primary,
  '--e-global-color-secondary': theme.colors.secondary,
  '--e-global-color-text': theme.colors.text,
  '--e-global-color-accent': theme.colors.accent,
  '--e-global-color-aa7315d': theme.colors.dark,
  '--e-global-color-c04339e': theme.colors.yellow,
  '--e-global-color-df30e16': theme.colors.gold,
  '--e-global-color-4f99b4a': theme.colors.black,
  '--e-global-color-629753e': theme.colors.white,
  '--e-global-color-5640c0f': theme.colors.transparent,
  '--e-global-color-b97f751': theme.colors.primary80,
  '--e-global-color-b35836b': theme.colors.darkBlue,
  '--e-global-color-fb18efe': theme.colors.teal,
  '--e-global-color-e4ba951': theme.colors.lightGray,
  '--e-global-color-2daa1f1': theme.colors.primary80Alt,
  '--e-global-color-4524d79': theme.colors.gray80
};

export type Theme = typeof theme; 