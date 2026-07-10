import { describe, it, expect } from 'vitest';
import { stageForTurnNumber, MAX_TURNS, STAGE_TURN_RANGES } from './interview';

describe('stageForTurnNumber', () => {
  it('returns INTRO for turn 1', () => {
    expect(stageForTurnNumber(1)).toBe('INTRO');
  });

  it('returns INTRO for turn 2', () => {
    expect(stageForTurnNumber(2)).toBe('INTRO');
  });

  it('returns TECHNICAL for turn 3', () => {
    expect(stageForTurnNumber(3)).toBe('TECHNICAL');
  });

  it('returns TECHNICAL for turn 9', () => {
    expect(stageForTurnNumber(9)).toBe('TECHNICAL');
  });

  it('returns BEHAVIORAL for turn 10', () => {
    expect(stageForTurnNumber(10)).toBe('BEHAVIORAL');
  });

  it('returns BEHAVIORAL for turn 15', () => {
    expect(stageForTurnNumber(15)).toBe('BEHAVIORAL');
  });

  it('returns WRAP_UP for turn 16', () => {
    expect(stageForTurnNumber(16)).toBe('WRAP_UP');
  });

  it('returns WRAP_UP for turns beyond MAX_TURNS', () => {
    expect(stageForTurnNumber(17)).toBe('WRAP_UP');
    expect(stageForTurnNumber(100)).toBe('WRAP_UP');
  });

  it('MAX_TURNS matches WRAP_UP start', () => {
    expect(MAX_TURNS).toBe(STAGE_TURN_RANGES.WRAP_UP[0]);
    expect(MAX_TURNS).toBe(STAGE_TURN_RANGES.WRAP_UP[1]);
  });
});
