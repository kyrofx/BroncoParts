import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#670001',
    },
    // You can also define secondary, error, warning, info, success colors here
    // For example:
    // secondary: {
    //   main: '#anotherColor',
    // },
  },
  // You can customize other theme aspects like typography, spacing, breakpoints, etc.
  // typography: {
  //   fontFamily: 'Roboto, Arial, sans-serif',
  // },
});

export default theme;
