-- migration_005_fix_roi_entry.sql
-- Fix: ROIs con detect_entry=False no generan eventos de entrada.
-- Sin entry events, no hay metricas ni reportes utiles.
UPDATE roi SET detect_entry = TRUE WHERE detect_entry = FALSE;
