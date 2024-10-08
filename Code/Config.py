import torch
from AA_features import features
# ==============================================
def linear_beta_schedule(b_0, b_T, T):
    return torch.linspace(b_0, b_T, T)
# ==============================================
def cosine_beta_schedule(b_0, b_T, T):
    steps = torch.arange(T + 1, dtype=torch.float32) / T
    alpha_bar = torch.cos((steps + 0.008) / 1.008 * torch.pi / 2) ** 2
    betas = torch.clip(1 - alpha_bar[1:] / alpha_bar[:-1], 0.0, 0.999)
    return torch.clip(betas, b_0, b_T)
# ==============================================
def sigmoid_beta_schedule(b_0, b_T, T, sigmoid_scaling=6):
    betas = torch.linspace(-sigmoid_scaling, sigmoid_scaling, T)
    betas = torch.sigmoid(betas)
    betas = (b_T - b_0) * betas + b_0
    return betas
# ==============================================
class config:
    # -------------------------------------------
    def __init__(self, 
                 T=25000, 
                 eta=0, 
                 tau=1, 
                 lr = 5e-7,
                 batch_size=256, 
                 num_layers=4, 
                 node_embed_size = 32,
                 edge_embed_size = 32, 
                 b_0 = 1e-4, 
                 b_T = 2e-2, 
                 scheduling = 'cosine'):
        # ----------------------------------
        self.T = T
        self.b_0 = b_0
        self.b_T = b_T
        self.num_features = int(len(features().AA_prop_keys))
        self.num_residues = 32
        self.learning_rate = lr
        self.batch_size = batch_size
        self.num_layers = num_layers
        self.device = torch.device('cuda:0')
        self.h_embed_size = node_embed_size
        self.edge_embed_size = edge_embed_size
        self.node_embed_size = node_embed_size
        self.in_feature_size = self.h_embed_size*2
        # ----------------------------------
        if scheduling == 'linear':
            self.scheduling = linear_beta_schedule(self.b_0, self.b_T, self.T)
        elif scheduling == 'cosine':
            self.scheduling = cosine_beta_schedule(self.b_0, self.b_T, self.T)
        elif scheduling == 'sigmoid':
            self.scheduling = sigmoid_beta_schedule(self.b_0, self.b_T, self.T)
        # --------------------------------------
        self.b_schedule = self.scheduling.to(self.device)
        self.a_schedule = (1 - self.b_schedule).to(self.device)
        self.alpha_bars = torch.cumprod(self.a_schedule, dim=0).to(self.device)
        self.alpha_prev_bars = torch.cat([torch.Tensor([1]).to(self.device),
                                          self.alpha_bars[:-1]])
        self.sigmas = torch.sqrt((1 - self.alpha_prev_bars) / (1 - self.alpha_bars)) * \
                      torch.sqrt(1 - (self.alpha_bars / self.alpha_prev_bars))

# ==============================================
def positional_embedding(device=torch.device('cuda:0')):
    res_index = torch.arange(config().num_residues).float().to(device)
    K = torch.arange(config().node_embed_size // 2, dtype=torch.float).to(device)
    div_term = torch.exp(K * -(torch.log(torch.tensor(10000.0)) / (config().node_embed_size // 2))).to(device)
    pos_embedding_sin = torch.sin(res_index[:, None] * div_term).to(device)
    pos_embedding_cos = torch.cos(res_index[:, None] * div_term).to(device)
    pos_embedd = torch.cat([pos_embedding_sin, pos_embedding_cos], dim=-1)
    return pos_embedd
# ==============================================
def load_checkpoint(model, optimizer, checkpoint_path):
    checkpoint = torch.load(checkpoint_path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']
    return model, optimizer, epoch, loss
# ==============================================
