from typing import Tuple, Union

import torch
from torch.nn import functional as F
from torchtyping import TensorType, patch_typeguard
from typeguard import typechecked

patch_typeguard()


@typechecked
class NeuralTPP(torch.nn.Module):
    """Neural Temporal Point Process class
    Args:
        hidden_dim (int): Number of history_emb dimensions.
    """

    def __init__(self, hidden_dim: int = 16):
        super(NeuralTPP, self).__init__()

        self.hidden_dim = hidden_dim

        # Single layer RNN for history embedding with tanh nonlinearity
        #######################################################
        # write here and replace the default
        self.embedding_rnn = torch.nn.RNN(input_size=2, hidden_size=hidden_dim, num_layers=1, batch_first=True,nonlinearity='tanh')
        #######################################################

        # Single layer neural network to predict mu and log(sigma)
        #######################################################
        # write here and replace the default
        self.linear = torch.nn.Linear(hidden_dim, 2)
        #######################################################

        # value to be used for numerical problems
        self.eps = 1e-8

    def log_likelihood(
        self,
        times: TensorType[torch.float32, "batch", "max_seq_length"],
        mask: TensorType[torch.bool, "batch", "max_seq_length"],
    ) -> TensorType[torch.float32, "batch"]:
        """Compute the log-likelihood for a batch of padded sequences.
        Args:
            times (Tensor): Padded inter-event times,
                shape (batch_size, seq_len+1)
            mask (Tensor): Boolean mask that indicates which entries
                do NOT correspond to padding, shape (batch_size, seq_len+1)
        Returns:
            log_likelihood: Log-likelihood for each sample in the batch,
                shape (batch_size,)
        """
        # clamp for stability
        times = torch.clamp(times, min=self.eps)

        # get history_emb
        history_emb = self.embed_history(times)

        # get cond. distributions
        mu, sigma = self.get_distribution_parameters(history_emb)
        dist = self.get_distributions(mu, sigma)

        # calculate negative log_likelihood
        log_density = self.get_log_density(dist, times, mask)
        log_survival = self.get_log_survival_prob(dist, times, mask)

        log_likelihood = log_density + log_survival

        return log_likelihood

    def get_log_density(
        self,
        distribution: torch.distributions.LogNormal,
        times: TensorType[torch.float32, "batch", "max_seq_length"],
        mask: TensorType[torch.bool, "batch", "max_seq_length"],
    ) -> TensorType["batch"]:
        """Compute the log-density for a batch of padded sequences.
        Args:
            distribution (torch.distributions.LogNormal): instance of pytorch distribution class
            times (Tensor): Padded inter-event times,
                shape (batch_size, seq_len+1)
            mask (Tensor): Boolean mask that indicates which entries
                do NOT correspond to padding, shape (batch_size, seq_len+1)
            B (int): batch size
            seq_len (int): max sequence length
        Returns:
            log_density: Log-density for each sample in the batch,
                shape (batch_size,)
        """
        # calculate log density
        #######################################################
        # write here and replace the default
        log_density = distribution.log_prob(times)
        log_density = log_density * mask
        log_density = log_density.sum(dim=1)
        #######################################################
        return log_density

    def get_log_survival_prob(
        self,
        distribution: torch.distributions.LogNormal,
        times: TensorType[torch.float32, "batch", "max_seq_length"],
        mask: TensorType[torch.bool, "batch", "max_seq_length"],
    ) -> TensorType["batch"]:
        """Compute the log-intensities for a batch of padded sequences.
        Args:
            distribution (torch.distributions.LogNormal): instance of pytorch distribution class
            times (Tensor): Padded inter-event times,
                shape (batch_size, seq_len+1)
            mask (Tensor): Boolean mask that indicates which entries
                do NOT correspond to padding, shape (batch_size, seq_len+1)
            B (int): batch size
            seq_len (int): max sequence length
        Returns:
            log_surv_last: Log-survival probability for each sample in the batch,
                shape (batch_size,)
        """
        # calculate log survival probability
        #######################################################
        # write here and replace the default
        cdf = distribution.cdf(times)
        surv_prob = 1 - cdf

        log_surv_prob = torch.log(surv_prob + self.eps)
        log_surv_prob = log_surv_prob * mask

        log_surv_last = log_surv_prob.sum(dim=1)
        log_surv_last = log_surv_prob[:,-1]
        #######################################################

        return log_surv_last

    def encode(
        self, times: TensorType[torch.float32, "batch", "max_seq_length"]
    ) -> TensorType[torch.float32, "batch", "max_seq_length", 2]:
        #######################################################
        # write here and replace the default
        log_times = torch.log(times + self.eps)
        x = torch.stack((times, log_times), dim=-1)
        #######################################################
        return x

    def embed_history(
        self, times: TensorType[torch.float32, "batch", "max_seq_length"]
    ) -> TensorType[torch.float32, "batch", "max_seq_length", "history_emb_dim"]:
        """Embed history for a batch of padded sequences.
        Args:
            times: Padded inter-event times,
                shape (batch_size, max_seq_length)
        Returns:
            history_emb: history_emb embedding of the history,
                shape (batch_size, max_seq_length, embedding_dim)
        """

        #######################################################
        # write here and replace the default
        encoded = self.encode(times)
        h_0 = torch.zeros((1, times.size(1), self.hidden_dim), device=times.device)
        history_emb, _ = self.embedding_rnn(encoded, h_0)
        #######################################################

        return history_emb

    def get_distributions(
        self,
        mu: TensorType[torch.float32, "batch", "max_seq_length"],
        sigma: TensorType[torch.float32, "batch", "max_seq_length"],
    ) -> Union[torch.distributions.LogNormal, None]:
        """Get log normal distribution given mu and sigma.
        Args:
            mu (tensor): predicted mu (batch, max_seq_length)
            sigma (tensor): predicted sigma (batch, max_seq_length)

        Returns:
            Distribution: log_normal
        """

        #######################################################
        # write here and replace the default
        log_norm_dist = torch.distributions.LogNormal(mu, sigma)
        #######################################################
        return log_norm_dist

    def get_distribution_parameters(
        self,
        history_emb: TensorType[
            torch.float32, "batch", "max_seq_length", "history_emb_dim"
        ],
    ) -> Tuple[
        TensorType[torch.float32, "batch", "max_seq_length"],
        TensorType[torch.float32, "batch", "max_seq_length"],
    ]:
        """Compute distribution parameters.
        Args:
            history_emb (Tensor): history_emb tensor,
                shape (batch_size, seq_len+1, C)
        Returns:
            Parameter (Tuple): mu, sigma
        """
        #######################################################
        # write here and replace the default
        output = self.linear(history_emb)
        mu, sigma_log = torch.split(output, 1, dim=-1)
        sigma = torch.exp(sigma_log.squeeze(-1))
        mu = mu.squeeze(-1)
        #######################################################
        return mu, sigma

    def forward(self):
        """
        Not implemented
        """
        pass
