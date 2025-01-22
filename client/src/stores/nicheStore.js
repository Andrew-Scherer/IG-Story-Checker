import { create } from 'zustand';
import { niches } from '../api';

const useNicheStore = create((set, get) => ({
  // State
  niches: [],
  selectedNicheId: null,
  loading: false,
  error: null,
  
  // Actions
  fetchNiches: async () => {
    try {
      console.log('=== Fetching Niches ===');
      console.log('1. Setting loading state...');
      set({ loading: true, error: null });
      
      console.log('2. Making API request to /api/niches...');
      const response = await niches.list();
      console.log('3. API Response:', response);
      
      console.log('4. Updating store with niches...');
      set({ niches: response });
      console.log('5. Store updated successfully');
    } catch (error) {
      console.error('!!! Error fetching niches !!!');
      console.error('Error details:', error);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      if (error.response) {
        console.error('Server response:', error.response);
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
      }
      set({ error: error.message });
    } finally {
      set({ loading: false });
    }
  },
  
  setSelectedNicheId: (id) => {
    set({ selectedNicheId: id });
  },
  
  createNiche: async (data) => {
    try {
      set({ loading: true, error: null });
      const response = await niches.create(data);
      set(state => ({
        niches: [...state.niches, response]
      }));
      return response;
    } catch (error) {
      console.error('Failed to create niche:', error);
      set({ error: error.message });
      throw error;
    } finally {
      set({ loading: false });
    }
  },
  
  updateNiche: async (id, data) => {
    try {
      set({ loading: true, error: null });
      const response = await niches.update(id, data);
      set(state => ({
        niches: state.niches.map(n => 
          n.id === id ? response : n
        )
      }));
      return response;
    } catch (error) {
      console.error('Failed to update niche:', error);
      set({ error: error.message });
      throw error;
    } finally {
      set({ loading: false });
    }
  },
  
  deleteNiche: async (id) => {
    try {
      set({ loading: true, error: null });
      await niches.delete(id);
      set(state => ({
        niches: state.niches.filter(n => n.id !== id),
        selectedNicheId: state.selectedNicheId === id ? null : state.selectedNicheId
      }));
    } catch (error) {
      console.error('Failed to delete niche:', error);
      set({ error: error.message });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  getNiches: () => get().niches
}));

export default useNicheStore;
