import { createClient } from '@supabase/supabase-js'

const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN3cXhjaHVxdWV1eGJycGRib21kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTk2MDIwNDYsImV4cCI6MjAzNTE3ODA0Nn0.k-gayiU6poeGSpEzYhwC5aD52tF3K_FDM6w2bPzWt8g'
const supabaseUrl = 'https://swqxchuqueuxbrpdbomd.supabase.co'

export const supabase = createClient(supabaseUrl, supabaseKey)
