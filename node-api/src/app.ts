import express from 'express';
import taskRoutes from './routes/taskRoutes';
import { errorHandler } from './middlewares/errorHandler';
import cors from 'cors';

const app = express();
// Manual CORS headers to ensure they're always added
app.use(cors());
app.use(express.json());
app.use('/api/tasks', taskRoutes);

app.use(errorHandler);

export default app;
