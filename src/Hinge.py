import torch
import torch.nn as nn
import torch.nn.functional as F

class HINGE(nn.Module):
    def __init__(self, num_entities, num_relations, embedding_dim=100, nf=400):
        """
        num_entities: number of unique entities (for head, tail, and value entities)
        num_relations: number of unique relations (for base relations and keys)
        embedding_dim: K, the dimension of the embeddings.
        nf: number of filters for the convolutional layers.
        """
        super(HINGE, self).__init__()
        self.embedding_dim = embedding_dim
        self.nf = nf
        
        # Embedding layers for entities and relations.
        self.ent_emb = nn.Embedding(num_entities, embedding_dim)
        self.rel_emb = nn.Embedding(num_relations, embedding_dim)
        # Initialize embeddings (e.g., Xavier initialization)
        nn.init.xavier_uniform_(self.ent_emb.weight)
        nn.init.xavier_uniform_(self.rel_emb.weight)
        
        # CNN for base triplet (h, r, t)
        # Input image: shape (batch, 1, 3, embedding_dim)
        self.triplet_conv = nn.Conv2d(in_channels=1, out_channels=nf, kernel_size=(3, 3))
        
        # CNN for each quintuple (h, r, t, k, v)
        # Input image: shape (batch, 1, 5, embedding_dim)
        self.quintuple_conv = nn.Conv2d(in_channels=1, out_channels=nf, kernel_size=(5, 3))
        
        # Fully connected layer to produce final score from merged feature vector.
        # The dimension of each branch’s output after flattening is nf*(embedding_dim-2).
        self.fc = nn.Linear(nf * (embedding_dim - 2), 1)
    
    def conv_branch(self, x, conv_layer):
        """
        Apply a convolutional branch.
        x: tensor of shape (batch, height, embedding_dim)
        conv_layer: either self.triplet_conv or self.quintuple_conv.
        Returns: a flattened feature vector of shape (batch, nf*(embedding_dim-2))
        """
        # x shape: (batch, height, embedding_dim) -> add channel dim: (batch, 1, height, embedding_dim)
        x = x.unsqueeze(1)
        x = conv_layer(x)  # shape: (batch, nf, 1, embedding_dim-2)
        x = F.relu(x)
        x = x.squeeze(2)   # shape: (batch, nf, embedding_dim-2)
        x = x.view(x.size(0), -1)  # flatten to (batch, nf*(embedding_dim-2))
        return x

    def forward(self, h, r, t, key_value_pairs=None):
        """
        Forward pass.
        h, r, t: indices for the head, base relation, and tail.
        key_value_pairs: Optional tensor of shape (batch, n, 2) with (k, v) indices.
        If None, the model treats the fact as a triple fact.
        Returns: predicted score (lower is better) for the fact.
        """
        # Embed the base triplet.
        h_emb = self.ent_emb(h)   # (batch, embedding_dim)
        r_emb = self.rel_emb(r)   # (batch, embedding_dim)
        t_emb = self.ent_emb(t)   # (batch, embedding_dim)
        
        # Create triplet “image”: stack h, r, t -> (batch, 3, embedding_dim)
        triplet_input = torch.stack([h_emb, r_emb, t_emb], dim=1)
        triplet_feature = self.conv_branch(triplet_input, self.triplet_conv)  # (batch, nf*(embedding_dim-2))
        
        # If no key-value pairs are provided, use only the base triplet.
        if key_value_pairs is None:
            merged_feature = triplet_feature
        else:
            # key_value_pairs: shape (batch, n, 2)
            batch_size, num_pairs, _ = key_value_pairs.size()
            # Get embeddings for keys (relations) and values (entities)
            keys = key_value_pairs[:, :, 0]  # (batch, n)
            values = key_value_pairs[:, :, 1]  # (batch, n)
            key_emb = self.rel_emb(keys)       # (batch, n, embedding_dim)
            value_emb = self.ent_emb(values)   # (batch, n, embedding_dim)
            
            # Expand base triplet embeddings to (batch, n, embedding_dim)
            h_exp = h_emb.unsqueeze(1).expand(-1, num_pairs, -1)
            r_exp = r_emb.unsqueeze(1).expand(-1, num_pairs, -1)
            t_exp = t_emb.unsqueeze(1).expand(-1, num_pairs, -1)
            
            # Stack to form quintuple: [h, r, t, k, v] of shape (batch, n, 5, embedding_dim)
            quintuple_input = torch.stack([h_exp, r_exp, t_exp, key_emb, value_emb], dim=2)
            # Reshape to (batch*n, 5, embedding_dim)
            quintuple_input = quintuple_input.view(-1, 5, self.embedding_dim)
            quintuple_feature = self.conv_branch(quintuple_input, self.quintuple_conv)
            # Reshape back to (batch, n, nf*(embedding_dim-2))
            quintuple_feature = quintuple_feature.view(batch_size, num_pairs, -
